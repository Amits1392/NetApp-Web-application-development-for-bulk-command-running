# NetApp-Web-application-development-for-bulk-command-running
NetApp Bulk Command Execution Web Portal  A Flask-based web application built for NetApp administrators to run bulk CLI commands across multiple NetApp clusters from a centralized web UI.  This tool helps storage teams avoid logging into multiple clusters manually.
Use this as your **GitHub README / public repo description** for your **NetApp Web Command Portal** project.

This explains everything clearly so any public user can clone and run it.

---

# NetApp Bulk Command Execution Web Portal

A Flask-based web application built for NetApp administrators to run bulk CLI commands across multiple NetApp clusters from a centralized web UI.

This tool helps storage teams avoid logging into multiple clusters manually.

---

# Problem Statement

In enterprise environments:

* 40+ Shipping clusters
* 30+ Cloud Volumes ONTAP clusters
* multiple common clusters

Storage admins waste time:

* logging into each cluster manually
* running repetitive commands
* collecting outputs manually
* sharing reports manually

This portal automates that process.

---

# What This Tool Does

User logs into web portal → selects clusters → enters commands → executes commands on all selected clusters → generates reports → optionally emails report.

---

# Features

✅ Secure web login

✅ Admin user creation

✅ User deletion management

✅ Role-based access

✅ Multi-cluster command execution

✅ Bulk command execution

✅ Category-based cluster grouping:

* Shipping
* CVO
* Common

✅ Select all by category

✅ HTML report generation

✅ Excel report generation

✅ Email integration

✅ SSH key-based authentication

✅ Attractive dashboard UI

✅ Session timeout/logout

---

# Architecture Flow

```text
User Browser
     |
     v
Flask Web Portal
     |
     v
SSH Connection via Paramiko
     |
     v
NetApp Clusters
     |
     v
Generate HTML + Excel Report
     |
     v
Email Report
```

---

# Use Cases

---

## Bulk Health Validation

Run:

```text
node show
storage aggregate show
volume show
```

Across 50 clusters.

---

## SnapMirror Validation

Run:

```text
snapmirror show
```

Across DR clusters.

---

## Pre/Post Upgrade Validation

Run:

```text
system node image show
version
```

---

## Capacity Audit

Run:

```text
volume show
storage aggregate show
```

---

## Network Troubleshooting

Run:

```text
network port show
network interface show
```

---

# Folder Structure

```bash
NetappWebPortal/
│
├── app.py
├── send_mail.py
├── users.db
├── clusters.csv
│
├── reports/
│   ├── output.html
│   ├── output.xlsx
│
├── logs/
│
└── templates/
    ├── login.html
    ├── dashboard.html
    ├── create_user.html
    ├── manage_users.html
    ├── message.html
```

---

# clusters.csv Format

```csv
cluster_name,ip,category
ship-cluster1,10.1.1.1,shipping
ship-cluster2,10.1.1.2,shipping
cvo-prod1,10.1.1.3,cvo
common-prod1,10.1.1.4,common
```

---

# Supported Categories

### Shipping

For logistics/warehouse clusters

---

### CVO

For Cloud Volumes ONTAP clusters

---

### Common

For shared enterprise clusters

---

# Prerequisites

Install:

* Python 3.8+
* SSH access to NetApp clusters
* Flask
* Pandas
* Paramiko
* Openpyxl
* Bcrypt

---

# Install Dependencies

```bash
pip install flask paramiko pandas openpyxl bcrypt
```

---

# Offline Installation (Corporate Restricted Servers)

Download packages:

```bash
pip download flask paramiko pandas openpyxl bcrypt --platform manylinux2014_x86_64 --python-version 3.12 --only-binary=:all: -d netapp_portal_pkg
```

Copy to server:

```bash
scp -r netapp_portal_pkg user@server:/home/user/
```

Install offline:

```bash
pip install --no-index --find-links=netapp_portal_pkg flask paramiko pandas openpyxl bcrypt
```

---

# SSH Configuration

Generate SSH key:

```bash
ssh-keygen -t rsa
```

Default key:

```bash
~/.ssh/id_rsa
```

---

# Copy Public Key to NetApp Clusters

```bash
ssh-copy-id netappreadonly@cluster-ip
```

---

# Recommended Security Setup

Create dedicated read-only user in NetApp:

Example:

```text
netappreadonly
```

This account should only have:

* show permissions
* readonly CLI access

Avoid using cluster admin account.

---

# Web Admin Login

Default:

```text
Username: nas-admin
Password: Netapp1!
```

Change password after deployment.

---

# Run Application

```bash
python3 app.py
```

Access:

```text
http://server-ip:5000
```

---

# Run in Background

```bash
nohup python3 app.py > portal.log 2>&1 &
```

---

# Production Deployment (Recommended)

Use Gunicorn:

```bash
pip install gunicorn
```

Run:

```bash
gunicorn -w 4 -b 0.0.0.0:5000 app:app
```

Optional reverse proxy:

Nginx

---

# Email Configuration

Update `send_mail.py`

For Gmail:

```python
smtp.gmail.com
port 587
```

For enterprise SMTP:

```python
mail.company.com
port 25
```

---

# How Users Use Portal

---

### Step 1

Login to portal

---

### Step 2

Select cluster category:

* Shipping
* CVO
* Common

---

### Step 3

Select clusters

---

### Step 4

Enter commands

Example:

```text
node show
volume show
snapmirror show
```

---

### Step 5

Enter email

---

### Step 6

Click:

```text
Run Commands
```

---

### Step 7

Receive:

* HTML report
* Excel report

---

# Security Features

✅ Password hashing using bcrypt

✅ Session logout

✅ Admin role restriction

✅ User deletion protection

✅ Cannot delete main admin user

✅ SSH key authentication

---

# Limitations

* Currently CLI-based only
* No REST API integration
* No MFA
* No approval workflow

---

# Future Enhancements

* REST API integration with NetApp ONTAP API
* Slack alerts
* Microsoft Teams alerts
* Kubernetes deployment
* Docker deployment
* Role approval workflows
* Command templates

---

# Best Use Cases

This tool is highly useful for:

* Storage teams
* Cloud storage teams
* Operations teams
* NetApp admins
* Upgrade teams
* DR teams

Managing large NetApp environments.
# Author

Built for enterprise-scale NetApp automation to reduce repetitive manual operational work.
