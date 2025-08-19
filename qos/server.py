#reçoit l'image
import socket
import os
def receive_image():
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.bind(('0.0.0.0',5000))     #écoute sur le port 5000
    server.listen(1)
    print("serveur en attente de connexion...")

    conn, addr = server.accept()
    print(f"connecté à {addr}")

    #Recevoir le nom du fichier
    file_name = conn.recv(1024).decode()
    with open(f"received_{file_name}", 'wb') as f:
        #recevoir les données de l'image 
        while True:
            data = conn.recv(1024)
            if not data:
                break
            f.write(data)
    
    print(f"Image {file_name} reçue avec succès")
    conn.close()
    server.close()

if __name__ == "__main__":
    receive_image()