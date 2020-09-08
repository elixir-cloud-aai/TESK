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

* Make it writable. In `/etc/vsftpd.conf` set:

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
  sudo nano /etc/vsftpd.conf
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
  If FTP server fails to start, investigate by trying to start it manually:
  ```
  sudo vsftpd
  ```
* You may need to configure or disable firewall (such as `ufw`)
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

* Configure credentials and hostIP for FTP using the Helm chart according to instructions.
```
 ftp.hostip:
```
`hostIP` needs to be set to the IP, where containers running in your K8s see your services running on localhost.
For `docker` driver, it seems to be `172.30.0.1` (on Linux). For minikube with a VM driver (such as virtualbox), you can check the IP by running:
```
minikube ssh "ping host.minikube.internal"
```


* Create the task:

  ```
  cd examples/
  $ ./taskCreate localftp/taskWithIO.json
  ```
* If you want to run `cwl-tes` locally with the locally installed FTP server, you need a couple more tricks:

- You need a `hosts` entry with
```
127.0.0.1 ftp
```
so that both cwl-tes and TESK see the local FTP at the same address.
- You need a `.netrc` file.   
```
machine ftp
login tesk
password <tesk-password>
```
It needs to be readable only to the owner
```
chmod 600 ~/.netrc
```
- Finally, you can run a workflow:
A good workflow to test your setup is: https://github.com/uniqueg/cwl-example-workflows.git.
which you need to clone

Then run the following command:
```
cwl-tes --tes http://minikube_ip:node_port  --remote-storage-url ftp://ftp/home/tesk hashsplitter-workflow.cwl hashsplitter-test.yml
```

- If the workflow uses FTP inputs, adjust them, so they point to existing files on your FTP server.

For example in the `hashsplitter-test.yml` from the workflow above make the following changes and also
make sure the input.txt file has been uploaded to your FTP.
```
input:
  class: File
  path: ftp://ftp/home/tesk/input.txt
```
- Running the above workflow and passing a local file with `--input` parameter (so letting `cwl-tes` upload an input file to FTP) fails for the proposed FTP setup. Most probably this functionality works only with chroot enabled on FTP server. 
