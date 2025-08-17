import paramiko

# === Config ===
hosts = [
    ("192.168.0.17", "Storage"),
    ("192.168.0.13", "Ingestion"),
    ("192.168.0.11", "Databases"),
]
username = "mike"      # Change to your SSH username
key_file = "/home/mike/.ssh/id_rsa"  # Path to your SSH private key

# === Function to run command over SSH ===
def run_df(host, label):
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    try:
        ssh.connect(hostname=host, username=username)
        stdin, stdout, stderr = ssh.exec_command("df -h --output=source,size,used,avail -x tmpfs -x devtmpfs")
        output = stdout.read().decode().strip().split("\n")[1:]  # Skip header
        ssh.close()

        rows = []
        for line in output:
            parts = line.split()
            if len(parts) >= 4:
                fs, total, used, avail = parts[0], parts[1], parts[2], parts[3]
                rows.append((label, fs, total, used, avail))
        return rows
    except Exception as e:
        return [(label, "ERROR", "N/A", str(e), "N/A")]

# === Collect data ===
table_data = []
for host, label in hosts:
    table_data.extend(run_df(host, label))

# === Print table ===
print(f"{'VM':<12} {'Filesystem':<20} {'Total':<10} {'Used':<10} {'Available':<10}")
print("-" * 70)
for row in table_data:
    print(f"{row[0]:<12} {row[1]:<20} {row[2]:<10} {row[3]:<10} {row[4]:<10}")
