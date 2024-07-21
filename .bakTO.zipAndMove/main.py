# coding:utf-8
import paramiko
import os
import warnings
from colorama import Fore, Style, init


def move():
    init(autoreset=True)
    # CryptographyDeprecationWarning uyarılarını bastır
    from cryptography.utils import CryptographyDeprecationWarning

    warnings.filterwarnings("ignore", category=CryptographyDeprecationWarning)

    # Sunucu bilgileri
    server_ip = 'YOUR_SERVER_IP'  # Sunucunun IP adresini buraya yazın
    username = 'SERVER_USERNAME'  # Sunucuda SSH ile bağlanacak kullanıcı adı
    password = 'SERVER_PASSWORD'  # Kullanıcının şifresi
    remote_directory = r'PATH/TO/RD'  # Uzak sunucudaki dosya yolu
    local_directory = os.path.expanduser(r'PATH/TO/LOCAL/DIRECTORY')  # Yerel bilgisayardaki dosya yolu

    # SSH ile sunucuya bağlan
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())

    try:
        ssh.connect(server_ip, username=username, password=password, timeout=60)

        # SFTP oturumu başlat
        sftp = ssh.open_sftp()

        # Uzak dizindeki dosyaları listele
        files = sftp.listdir_attr(remote_directory)

        # .bak uzantılı dosyaları filtrele ve en yakın değiştirilme tarihine sahip olanı bul
        bak_files = [f for f in files if f.filename.endswith('.BAK')]
        if not bak_files:
            print('Uzak sunucuda .bak uzantılı dosya bulunamadı.')
            exit()

        latest_file = max(bak_files, key=lambda x: x.st_mtime)

        # Uzak sunucuda .bak dosyasını zip olarak sıkıştır
        remote_file_path = os.path.join(remote_directory, latest_file.filename)
        zip_filename = latest_file.filename.replace('.BAK', '.zip')
        remote_zip_path = os.path.join(remote_directory, zip_filename)

        # Zip dosyasının mevcut olup olmadığını kontrol et
        zip_check_command = f'if (Test-Path "{remote_zip_path}") {{Write-Output "exists"}} else {{Write-Output "not exists"}}'
        stdin, stdout, stderr = ssh.exec_command(f'powershell.exe {zip_check_command}')
        zip_exists = stdout.read().strip().decode()

        if zip_exists == "exists":
            # Zip dosyası varsa, üzerine yazmak için -Force parametresiyle sıkıştır
            compress_command = f'Compress-Archive -LiteralPath "{remote_file_path}" -DestinationPath "{remote_zip_path}" -Force'
        else:
            # Zip dosyası yoksa, sadece oluştur
            compress_command = f'Compress-Archive -LiteralPath "{remote_file_path}" -DestinationPath "{remote_zip_path}"'

        stdin, stdout, stderr = ssh.exec_command(f'powershell.exe {compress_command}')
        stdout.channel.recv_exit_status()  # Komutun tamamlanmasını bekle

        # Sıkıştırılmış dosyayı yerel bilgisayara indir
        local_zip_path = os.path.join(local_directory, zip_filename)
        sftp.get(remote_zip_path, local_zip_path)

        # Bağlantıları kapat
        sftp.close()
        ssh.close()

        print(f'{latest_file.filename} başarıyla sıkıştırıldı ve {local_zip_path} olarak indirildi.')

    except Exception as e:
        print(f'Bağlantı hatası: {e}')
    finally:
        ssh.close()

    print("Aktarım işlemi tamamlandı.")


def run():
    while True:

        user = int(input(Fore.GREEN+"Uzak serverdaki yedeği aktarmak için 1 yazın ve entera basın."))

        if user == 1:
            print("Aktarım işlemi başladı.")
            print("------------------------")
            move()
            break
        else:
            print("Hatalı bir komut girdiniz! Tekrar deneyin")


run()
