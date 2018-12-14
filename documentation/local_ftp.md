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
