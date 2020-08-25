How to use local FTP
--------------------

* Create a new user on the host

  ```
  sudo adduser tesk
  ```

* Install [vsftpd](https://help.ubuntu.com/lts/serverguide/ftp-server.html.en)

  ```
  sudo apt install vsftpd
  ```

* Make it writable

  ```
  write_enable=YES
  ```

* To configure TLS with vsftpd (Optional),
  if you are planning to use cwl-tes, then you have to add TLS certificate to vsftpd.
  ```
  sudo mkdir /etc/ssl/private
  sudo openssl req -x509 -nodes -days 365 -newkey rsa:2048 -keyout /etc/ssl/private/vsftpd.pem -out /etc/ssl/private/vsftpd.pem
  ```
  Open the vsftpd configuration file as root:
  ```
  sudo nano /etc/vsftpd/vsftpd.conf
  ```
  Now, specify the location of our certificate, key files and other configurations to the end of the file.
  ```
  rsa_cert_file=/etc/ssl/private/vsftpd.pem
  rsa_private_key_file=/etc/ssl/private/vsftpd.pem
  ssl_enable=YES
  allow_anon_ssl=NO
  force_local_data_ssl=NO
  force_local_logins_ssl=NO
  ssl_tlsv1=YES
  ssl_sslv2=NO
  ssl_sslv3=NO
  require_ssl_reuse=NO
  ssl_ciphers=HIGH
  ```
  Save and close the file.
   Restart vsftpd to enable our changes
   ```
   sudo /etc/init.d/vsftpd restart
   ```


* Edit the input and output URLs in the task's JSON (e.g.: `examples/localftp/taskWithIO.json`):

  ```
  "inputs": [
    {
      "description": "Downloading a single file from FTP",
      "name": "File from FTP",
      "path": "/tes/input",
      "type": "FILE",
      "url": "ftp://ftp/home/tesk/input.txt"   <= here
                                                  You have to use absolute paths.
                                                  Maybe because I'm not using `chroot_local_user` in FTP?
    }

  "outputs": [
    {
      "description": "Example of uploading a directory to FTP",
      "name": "Dir to FTP",
      "path": "/tes",
      "type": "DIRECTORY",
      "url": "ftp://ftp/home/tesk/output"			<= and here
    }
  ```

* Configure credentials, service and endpoint:

    1. `cd deployment/localftp/`

    2. Edit `config.ini`.

    3. Generate the YAMLs:

        ```
        $ ../scripts/configure
        ['ftp-service.yaml', 'ftp-secret.yaml', 'ftp-endpoint.yaml']
        ```

    4. Create the stuff:

       ```
       kubectl create -f .
       ```

* Create the task:

  ```
  cd examples/
  $ ./taskCreate localftp/taskWithIO.json
  ```
