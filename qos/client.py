#envoi l'image
import socket
import os

def send_image(image_path, server_ip):
    client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    client.connect((server_ip, 5000))  

    #envoyer le nom du fichier
    file_name = os.path.basename(image_path)
    client.send(file_name.encode())

    #envoyer les données de l'image 
    with open(image_path, 'rb') as f:
        while True:
            data = f.read(1024)
            if not data:
                break
            client.send(data)

    print(f"Image {file_name} envoyée avec succès")
    client.close()

if __name__ == "__main__":
    image_path = "image.jpg"     #chemin de l'image à envoyer 
    server_ip = "server-service"     #nom du service kubernetes du serveur
    send_image(image_path, server_ip)