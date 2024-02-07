#### PVC


1. `$ ./minikubeStart`

    Creates `/transferAtNode` mount at the node.

2. `$ kuCreate .`

This will create:

* a `pv`
* a `pvc` that uses the `pv`
* a `pod` that mounts the `pvc`

This pod will have the mount `/transfer` => `/home/tfga/workspace/cwl-tes`:

	$ ./clean
    -- Deleting all pods ------------------------------------
    pod "nginx-pod" deleted

    -- Deleting all pvc ------------------------------------
    persistentvolumeclaim "transfer-pvc" deleted

    -- Deleting all pv ------------------------------------
    persistentvolume "transfer-pv" deleted

    tfga@tfga ~/workspace/KubernetesTest/pvc
    $ kuCreate .
    pod/nginx-pod created
    persistentvolume/transfer-pv created
    persistentvolumeclaim/transfer-pvc created

    tfga@tfga ~/workspace/KubernetesTest/pvc
    $ kuSshPod nginx-pod
    root@nginx-pod:/# ls /transfer/
    LICENSE           old               tmp0k0657m1  tmp4a18kf4u  tmp9h0p6cg3  tmpbjm_c9lm  tmpf68dn9n8  tmpig_ryne9  tmpmmn0ia6i  tmpp9vkcipm  tmpt89n8hz8  tmpw61zd_kd  tmpxrbhu5mj  tmpyyjhvh8q
    README.md         requirements.txt  tmp0pzg_4xc  tmp4jsl4elr  tmp9zt9vkub  tmpbn9f3s3t  tmpfcxj9a_y  tmpiz83h1fm  tmpn47zb3m8  tmppi05vm5l  tmptms28mke  tmpwea3jpp6  tmpxrnnz9bj  tmpz0fg89z_
    build             runFileSystem     tmp1b46r818  tmp4qfxl_6k  tmp_f9xuo8k  tmpc5y3_h7w  tmpfuup87gk  tmpj7f96z1r  tmpn9f2w3lj  tmpplw4y2nn  tmpu25kek04  tmpwjeajmv6  tmpxuhnrw8n  tmpzgouou8q
    cwl-tes           runFunnel         tmp2m8non62  tmp57zvcdsl  tmp_ngu1f6g  tmpcxpn_zmu  tmpg0m9rffx  tmpjty8x2dl  tmpnb2d4ibx  tmppqgpkjsi  tmpu27kpb2e  tmpwq5ni_9v  tmpxzi574au  tmpzgx87pcz
    cwl_tes           runTesDev+Ftp     tmp2mck1kr9  tmp6llnimfl  tmp_zio3bq9  tmpd25x5s55  tmpg2iwsv7s  tmpk1aa5z63  tmpnf4uazrx  tmpquo3o00v  tmpupko0xrx  tmpws_ce7sy  tmpy1883fph  tox.ini
    cwl_tes.egg-info  setup.py          tmp2pnkovzz  tmp77zykmun  tmpab8tvnq_  tmpda_r6p8_  tmpgpcozofq  tmpk6gju6xl  tmpnq_qbh6w  tmpr1ciykyp  tmpusj6yl5b  tmpx1m3dmmy  tmpy1vzo358  unify
    debug.log         tests             tmp2th8wyn_  tmp78nw56aj  tmpah7u70t8  tmpdcv4pwg3  tmpgq80j8u5  tmpkpe3ipse  tmpoefw5ujx  tmprhfwrhy7  tmpve0cce76  tmpx31o4ylu  tmpy6p_gwpm  verbose.log
    dist              tmp049iugiv       tmp36ryoi5x  tmp835xzwq_  tmpazcfpcik  tmpdk2aq8tc  tmph875ges2  tmpktik6m0v  tmpolb1fklc  tmpsfzx43fd  tmpvxt19l8r  tmpx5wnwpoe  tmpy6tmx0rg
    funnel-work-dir   tmp06oyrxvw       tmp3yxlshpt  tmp8onbqh8f  tmpbe78f6el  tmpdutg8ng_  tmphrtip1o8  tmpld1j21ye  tmpoxvg9xpl  tmpslx5l0rl  tmpvyj9cppw  tmpx9opul51  tmpystuxi10

You can only do this with containers like nginx, because it _keeps running_ (it's a server). If you do it with `filer`, it will start and finish before you can `docker exec` into it.
You can only `docker exec` into running containers.
