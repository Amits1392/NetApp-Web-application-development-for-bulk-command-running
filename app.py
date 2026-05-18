from flask import Flask, render_template, request, redirect, session
from datetime import timedelta
import pandas as pd
import paramiko
import os
import time
import sqlite3
import bcrypt
import logging
from send_mail import send_email

app = Flask(__name__)
app.secret_key = "netapp_secure_portal"

# Session Config
app.config["PERMANENT_SESSION_LIFETIME"] = timedelta(minutes=15)
app.config["SESSION_PERMANENT"] = False

# NetApp SSH Config
NETAPP_USER = "ansible"
PRIVATE_KEY = "/home/ansible/.ssh/id_rsa"

# Load clusters
clusters_df = pd.read_csv("clusters.csv")

# Create folders
os.makedirs("logs", exist_ok=True)
os.makedirs("reports", exist_ok=True)

# Logging
logging.basicConfig(
    filename="logs/audit.log",
    level=logging.INFO,
    format="%(asctime)s - %(message)s"
)


# ---------------- LOGIN ----------------
@app.route("/")
def login():
    return render_template("login.html")


# ---------------- LOGIN VALIDATION ----------------
@app.route("/validate_login", methods=["POST"])
def validate_login():
    username = request.form["username"].strip()
    password = request.form["password"].strip()

    conn = sqlite3.connect("users.db")
    cur = conn.cursor()

    cur.execute(
        "SELECT password, role FROM users WHERE username=?",
        (username,)
    )

    user = cur.fetchone()
    conn.close()

    if user:
        stored_password = user[0]
        role = user[1]

        if bcrypt.checkpw(
            password.encode(),
            stored_password.encode()
        ):
            session.clear()
            session.permanent = False
            session["logged_in"] = True
            session["username"] = username
            session["role"] = role

            return redirect("/dashboard")

    return render_template(
        "login.html",
        error="Invalid username/password. Please login again."
    )


# ---------------- DASHBOARD ----------------
@app.route("/dashboard")
def dashboard():

    if not session.get("logged_in"):
        return redirect("/")

    shipping_clusters = clusters_df[
        clusters_df["category"] == "shipping"
    ]["cluster_name"].tolist()

    cvo_clusters = clusters_df[
        clusters_df["category"] == "cvo"
    ]["cluster_name"].tolist()

    common_clusters = clusters_df[
        clusters_df["category"] == "common"
    ]["cluster_name"].tolist()

    return render_template(
        "dashboard.html",
        shipping_clusters=shipping_clusters,
        cvo_clusters=cvo_clusters,
        common_clusters=common_clusters,
        role=session["role"]
    )

# ---------------- CREATE USER ----------------
@app.route("/create_user", methods=["GET", "POST"])
def create_user():

    if not session.get("logged_in"):
        return redirect("/")

    if session.get("role") != "admin":
        return redirect("/dashboard")

    if request.method == "POST":

        username = request.form["username"].strip()
        password = request.form["password"].strip()

        if not username or not password:
            return render_template(
                "message.html",
                color="red",
                message="Username and password cannot be empty."
            )

        hashed_password = bcrypt.hashpw(
            password.encode(),
            bcrypt.gensalt()
        ).decode()

        conn = sqlite3.connect("users.db")
        cur = conn.cursor()

        try:
            cur.execute(
                """
                INSERT INTO users(username,password,role)
                VALUES(?,?,?)
                """,
                (
                    username,
                    hashed_password,
                    "user"
                )
            )

            conn.commit()

            return render_template(
                "message.html",
                color="green",
                message="User created successfully."
            )

        except:
            return render_template(
                "message.html",
                color="red",
                message="User already exists."
            )

        finally:
            conn.close()

    return render_template("create_user.html")


# ---------------- MANAGE USERS ----------------
@app.route("/manage_users", methods=["GET", "POST"])
def manage_users():

    if not session.get("logged_in"):
        return redirect("/")

    if session.get("role") != "admin":
        return redirect("/dashboard")

    conn = sqlite3.connect("users.db")
    cur = conn.cursor()

    if request.method == "POST":

        username_to_delete = request.form["username"]

        if username_to_delete == "nas-admin":
            conn.close()

            return render_template(
                "message.html",
                color="red",
                message="Main admin user cannot be deleted."
            )

        if username_to_delete == session.get("username"):
            conn.close()

            return render_template(
                "message.html",
                color="red",
                message="You cannot delete your own active account."
            )

        cur.execute(
            "DELETE FROM users WHERE username=?",
            (username_to_delete,)
        )

        conn.commit()
        conn.close()

        return render_template(
            "message.html",
            color="green",
            message=f"{username_to_delete} deleted successfully."
        )

    cur.execute(
        "SELECT username FROM users"
    )

    users = cur.fetchall()

    conn.close()

    return render_template(
        "manage_users.html",
        users=users
    )


# ---------------- NETAPP COMMAND EXECUTION ----------------
def run_command(ip, command):

    try:
        ssh = paramiko.SSHClient()
        ssh.set_missing_host_key_policy(
            paramiko.AutoAddPolicy()
        )

        ssh.connect(
            hostname=ip,
            username=NETAPP_USER,
            key_filename=PRIVATE_KEY,
            timeout=20
        )

        shell = ssh.invoke_shell()

        time.sleep(2)

        if shell.recv_ready():
            shell.recv(65535)

        shell.send("set -rows 0\n")
        time.sleep(2)

        if shell.recv_ready():
            shell.recv(65535)

        shell.send(command + "\n")
        time.sleep(5)

        output = ""

        while shell.recv_ready():
            output += shell.recv(
                65535
            ).decode(
                errors="ignore"
            )

        ssh.close()

        lines = output.splitlines()
        cleaned_lines = []

        for line in lines:
            line = line.strip()

            if "::>" in line:
                continue

            if line.lower() == command.lower():
                continue

            if line == "":
                continue

            cleaned_lines.append(line)

        final_output = "\n".join(cleaned_lines)

        if not final_output:
            return "SUCCESS: Command executed successfully"

        return final_output

    except Exception as e:
        return f"FAILED: {str(e)}"


# ---------------- RUN COMMAND ----------------
@app.route("/run", methods=["POST"])
def run():

    if not session.get("logged_in"):
        return redirect("/")

    try:
        selected_clusters = request.form.getlist("clusters")
        commands = request.form["commands"].splitlines()
        email = request.form["email"].strip()

        if not selected_clusters:
            return render_template(
                "message.html",
                color="red",
                message="Please select at least one cluster."
            )

        if not email:
            return render_template(
                "message.html",
                color="red",
                message="Email is mandatory."
            )

        results = {}

        for cluster in selected_clusters:

            cluster_info = clusters_df[
                clusters_df["cluster_name"] == cluster
            ]

            if cluster_info.empty:
                continue

            ip = cluster_info.iloc[0]["ip"]

            cluster_results = {}

            for cmd in commands:

                cmd = cmd.strip()

                if not cmd:
                    continue

                output = run_command(ip, cmd)
                cluster_results[cmd] = output

            results[cluster] = cluster_results

        # Excel Report
        excel_file = "reports/output.xlsx"

        with pd.ExcelWriter(excel_file) as writer:

            for cluster, data in results.items():

                rows = []

                for cmd, output in data.items():
                    rows.append({
                        "Command": cmd,
                        "Output": output
                    })

                pd.DataFrame(rows).to_excel(
                    writer,
                    sheet_name=cluster[:31],
                    index=False
                )

        # HTML Report
        html_file = "reports/output.html"

        html_content = """
        <html>
        <head>
        <title>NetApp Command Report</title>

        <style>
        body{
            font-family:Arial;
            background:#f4f8fb;
            padding:20px;
        }

        .main-header{
            background:#0f172a;
            color:white;
            padding:20px;
            border-radius:12px;
            font-size:32px;
            font-weight:bold;
            margin-bottom:30px;
        }

        .cluster-box{
            background:white;
            padding:25px;
            margin-bottom:25px;
            border-radius:15px;
            box-shadow:0px 4px 15px rgba(0,0,0,0.2);
        }

        .cluster-title{
            font-size:28px;
            font-weight:bold;
            color:#1e3a8a;
            margin-bottom:20px;
        }

        .command-title{
            background:#2563eb;
            color:white;
            padding:12px;
            border-radius:8px;
            font-weight:bold;
            margin-top:20px;
            margin-bottom:10px;
        }

        pre{
            background:black;
            color:#00ff00;
            padding:20px;
            border-radius:10px;
            overflow-x:auto;
            white-space:pre-wrap;
            font-size:14px;
        }
        </style>

        </head>
        <body>

        <div class="main-header">
        NetApp Command Report
        </div>
        """

        for cluster, data in results.items():

            html_content += f"""
            <div class="cluster-box">
                <div class="cluster-title">{cluster}</div>
            """

            for cmd, output in data.items():

                html_content += f"""
                <div class="command-title">{cmd}</div>
                <pre>{output}</pre>
                """

            html_content += "</div>"

        html_content += """
        </body>
        </html>
        """

        with open(html_file, "w") as f:
            f.write(html_content)


        # Send Email
        mail_status = send_email(email)

        if mail_status is not True:
            return render_template(
                "message.html",
                color="red",
                message=f"Commands executed but email failed: {mail_status}"
            )

        logging.info(
            f"{session['username']} executed {commands} on {selected_clusters}"
        )

        return render_template(
            "message.html",
            color="green",
            message="Commands executed successfully. Reports generated and emailed successfully.",
            show_options=True
        )

    except Exception as e:
        return render_template(
            "message.html",
            color="red",
            message=f"Execution Failed: {str(e)}"
        )


# ---------------- LOGOUT ----------------
@app.route("/logout")
def logout():
    session.clear()
    return redirect("/")


if __name__ == "__main__":
    app.run(
        host="0.0.0.0",
        port=5000,
        debug=False
    )