import random
import string
import subprocess
import base64

# Function to generate WireGuard Keys
def generate_wireguard_keys():
    # Generate server private key
    server_private_key = subprocess.check_output(['wg', 'genkey']).strip().decode('utf-8')

    # Generate server public key
    cmd = f'echo {server_private_key} | wg pubkey'
    server_public_key = subprocess.run(cmd, stdout=subprocess.PIPE, shell=True, text=True).stdout.strip()

    return server_private_key, server_public_key

# Function to generate a random pre-shared key and base64 encode it
def generate_psk(length=32):
    characters = string.ascii_letters + string.digits
    psk = ''.join(random.choice(characters) for _ in range(length))
    return base64.b64encode(psk.encode()).decode()  # Base64 encode the PSK

# Function to generate peer configurations
def generate_peer_configurations(num_peers, use_psk, server_ip, server_public_key, server_endpoint, server_port, server_dns, common_psk):
    peer_configs = []

    # Server IP and public key for reference in peer configurations
    server_ip_parts = server_ip.split('.')

    # Ask whether peers should be part of the same subnet
    same_subnet = input("Do you want the peers to be part of the same subnet (y/n)? ").strip().lower()
    if same_subnet == 'y':
        same_subnet = True
    else:
        same_subnet = False

    for i in range(num_peers):
        peer_private_key, _ = generate_wireguard_keys()

        if use_psk:
            peer_psk = common_psk
        else:
            peer_psk = ""

        if same_subnet:
            # Peers are part of the same subnet
            peer_ip = f"{server_ip_parts[0]}.{server_ip_parts[1]}.{server_ip_parts[2]}.{i + 2}/24"
        else:
            # Peers have point-to-point connections
            peer_ip = f"{server_ip_parts[0]}.{server_ip_parts[1]}.{server_ip_parts[2]}.{i + 2}/32"

        peer_config = f"\n# Peer No. {i + 1}, copy below and create a peer.conf to be parsed\n\n" \
                      f"[Interface]\nAddress = {peer_ip}\nPrivateKey = {peer_private_key}\nDNS = {server_dns}\n\n" \
                      f"[Peer]\nPublicKey = {server_public_key}\nPresharedKey = {peer_psk}\n" \
                      f"Endpoint = {server_endpoint}:{server_port}\nAllowedIPs = 0.0.0.0/0, ::/0\n" \
                      f"PersistentKeepalive = 0\n"

        peer_configs.append(peer_config)

    return peer_configs

if __name__ == "__main__":
    # Ask the user for the server IP address
    server_ip = input("Enter the IP address for the server (e.g., x.x.x.1): ").strip()

    # Prompt for server settings
    server_endpoint = input("Enter server endpoint (IPv4 or DDNS): ").strip()
    server_port = "51820"  # Default WireGuard port for the server
    server_dns = input("Enter server DNS (optional): ").strip()

    # Generate server keys
    server_private_key, server_public_key = generate_wireguard_keys()

    # Ask the user if they want to use a pre-shared key for the peers
    use_psk_for_peers = input("Do you want to use a pre-shared key for the peers (y/n)? ").strip().lower()
    if use_psk_for_peers == 'y':
        use_psk = True
        # Generate a common pre-shared key for server and peers
        common_psk = generate_psk()
    else:
        use_psk = False
        common_psk = ""  # No common pre-shared key

    # Ask the user how many peers to generate
    num_peers = int(input("How many peers do you want to add? "))

# Generate server configuration without "Endpoint" for the server
    server_config = f"WireGuard Configs\n\nServer\n\n[Interface]\nAddress = {server_ip}/24\n" \
                f"PublicKey = {server_public_key}\nPrivateKey = {server_private_key}\n" \
                f"ListenPort = {server_port}\nDNS = {server_dns}\n\n"

    # Now, you pass the server_public_key to the generate_peer_configurations function
    peer_configs = generate_peer_configurations(num_peers, use_psk, server_ip, server_public_key, server_endpoint, server_port, server_dns, common_psk)

    # Save server and peer configurations to the same text file
    filename = "wg-server-and-peer-config.txt"
    data_to_save = server_config + "\n".join(peer_configs)
    with open(filename, 'w') as file:
        file.write(data_to_save)

    print(f"Data saved to {filename}")
