import cv2
from simple_facerec import SimpleFacerec
import time
import os
import shutil
import requests
import numpy as np
import pandas as pd # type: ignore
from googleapiclient.http import MediaFileUpload, MediaIoBaseDownload
from datetime import datetime
from googleapiclient.discovery import build
from google.oauth2 import service_account
from openpyxl import load_workbook

SCOPES = ['https://www.googleapis.com/auth/drive']
SERVICE_ACCOUNT_FILE = '/home/ggtxz/Documentos/source code/path/computacao-em-nuvem-424816-d2d9dda070b3.json'
PARENT_FOLDER_ID = "1MC3oiCzwLfwRApFIzV2AkN7jkQs0ludI"
DOWNLOAD_PATH_IMAGES = '/home/ggtxz/Documentos/source code/downloaded_images'
PATH_CSV = '/home/ggtxz/Documentos/source code/csv_files/chamada.csv'
DOWNLOAD_PATH_CSV = '/home/ggtxz/Documentos/source code/csv_files'
FALTAS_FOLDER_ID = "15BphelNVYDvmJH6gIVxdSwuc4SA3Q61l"


def autenticacao():
    creds = service_account.Credentials.from_service_account_file(
        SERVICE_ACCOUNT_FILE, scopes=SCOPES)
    service = build('drive', 'v3', credentials=creds)
    return service


def download_file(service, file_id, file_name, download_path):
    if not os.path.exists(download_path):
        os.makedirs(download_path)
    request = service.files().get_media(fileId=file_id)
    with open(os.path.join(download_path, file_name), 'wb') as file:
        downloader = MediaIoBaseDownload(file, request)
        done = False
        while not done:
            status, done = downloader.next_chunk()
            print(f"Download {int(status.progress() * 100)}%: {file_name}")


def get_file_id(service, folder_id, file_name):
    results = service.files().list(q=f"'{folder_id}' in parents and name='{file_name}'",
                                   pageSize=10, fields="files(id, name)").execute()
    items = results.get('files', [])
    if not items:
        raise FileNotFoundError(
            f"Arquivo {file_name} não encontrado na pasta de ID {folder_id}")
    return items[0]['id']


def download_images(service, folder_id, download_path):
    if not os.path.exists(download_path):
        os.makedirs(download_path)
    results = service.files().list(q=f"'{folder_id}' in parents",
                                   pageSize=100, fields="files(id, name)").execute()
    items = results.get('files', [])
    if not items:
        print('Nenhuma imagem encontrada.')
        return
    for item in items:
        file_id = item['id']
        file_name = item['name']
        download_file(service, file_id, file_name, download_path)

def capture_video():
    url = 'http://127.0.0.1:8000/'

    # Abre uma sessão para a captura do stream
    session = requests.Session()

    # Envia uma requisição GET para o servidor
    response = session.get(url, stream=True)

    if response.status_code != 200:
        print("Erro ao acessar a live")
    else:
        bytes_data = b''
        for chunk in response.iter_content(chunk_size=1024):
            bytes_data += chunk
            a = bytes_data.find(b'\xff\xd8')  # JPEG início
            b = bytes_data.find(b'\xff\xd9')  # JPEG fim
            
            if a != -1 and b != -1:
                jpg = bytes_data[a:b+2]
                bytes_data = bytes_data[b+2:]

                # Converte bytes em uma imagem numpy
                frame = cv2.imdecode(np.frombuffer(jpg, dtype=np.uint8), cv2.IMREAD_COLOR)

                # Salva o frame atual como uma imagem (opcional)
                cv2.imwrite('frame_capturado.jpg', frame)


                face_locations, face_names = sfr.detect_known_faces(frame)
                for face_loc, name in zip(face_locations, face_names):
                    y1, x2, y2, x1 = face_loc[0], face_loc[1], face_loc[2], face_loc[3]
                    if(name.strip().lower() not in recognized_faces and name.strip().lower() != 'unknown'):
                        recognized_faces.append(name.strip().lower())
                    cv2.putText(frame, name, (x1, y1 - 10),
                                cv2.FONT_HERSHEY_DUPLEX, 1, (0, 0, 200), 2)
                    cv2.rectangle(frame, (x1, y1), (x2, y2), (0, 0, 200), 4)
                cv2.imshow("Frame", frame)
                key = cv2.waitKey(1)
                if key == 27 or time.time() - start_time > run_time:
                    break

    cv2.destroyAllWindows()
    response.close()

# Autenticação para baixar as imagens
service = autenticacao()

# Verifica se as imagens já foram baixadas, caso não ele baixa
if not os.path.isdir(DOWNLOAD_PATH_IMAGES):
    print(f'O caminho {DOWNLOAD_PATH_IMAGES} não é uma pasta válida.')
    download_images(service, PARENT_FOLDER_ID, DOWNLOAD_PATH_IMAGES)

    
conteudo_pasta = os.listdir(DOWNLOAD_PATH_IMAGES)
    
if len(conteudo_pasta) == 0:  
    download_images(service, PARENT_FOLDER_ID, DOWNLOAD_PATH_IMAGES)

# Cria uma lista com os números de matrículas dos alunos dessa turma
alunos = {
    'matriculas': []
}
for i in range(0, len(conteudo_pasta)):
    alunos['matriculas'].append(conteudo_pasta[i].split('.')[0])

# Verifica se o arquivo .csv com as matrículas existe
if not os.path.isdir(DOWNLOAD_PATH_CSV):
    print(f'O caminho {DOWNLOAD_PATH_CSV} não é uma pasta válida.')
    

dataframe_matriculas = pd.DataFrame(alunos)

# Fazer o "encode" das imagens para reconhecer
sfr = SimpleFacerec()
sfr.load_encoding_images(DOWNLOAD_PATH_IMAGES)

recognized_faces = []  # Lista para armazenar os nomes das imagens reconhecidas
start_time = time.time()
run_time = 20  # Tempo de execução em segundos

while True:
    hora = datetime.now().strftime('%H:%M')
    if True:
        capture_video()
        break

    if hora == '19:45':
        capture_video()
        break
    

cv2.destroyAllWindows()

# Normalizar nomes das faces reconhecidas
recognized_faces = [name.strip().lower() for name in recognized_faces]

lista_de_presenca = []
#print(dataframe_matriculas[data_atual])
for aluno in dataframe_matriculas['matriculas']:
    if aluno.strip().lower() in recognized_faces:
        lista_de_presenca.append('P')
        print(f'Aluno {aluno} presente')
    else:
        lista_de_presenca.append('F')
        print(f'Aluno {aluno} ausente')

data_atual = datetime.today().strftime("%m/%d/%Y")

dataframe_matriculas[data_atual] = lista_de_presenca

dataframe_matriculas.to_csv(PATH_CSV, sep=',', index=False, encoding='utf-8')

# Atualizar o arquivo csv no Google Drive (substituir o existente)
faltas_file_id = get_file_id(service, FALTAS_FOLDER_ID, "chamada.csv")
faltas_file_path = os.path.join(DOWNLOAD_PATH_CSV, "chamada.csv")
media_faltas = MediaFileUpload(
    faltas_file_path, mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
service.files().update(fileId=faltas_file_id,
                       media_body=media_faltas, fields='id').execute()
