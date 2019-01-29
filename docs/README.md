# Útmutató

Készítette: Török Máté

## Előkészület

Javasolt egy Linux gép használata egy web kamerával. A program Raspberry Pi-ra készült de például MacOsx alatt fejlesztettem, tehát a lényeg, hogy ha lehet Unix gépről dolgozzunk. Python 3 kell hozzá és a `requirements.txt`-ben megadott pip package-ek. Azért nem egy Raspberry Pi-t javaslok kipróbáláshoz, mert annak beállíátása körülményesebb, hiszen ARM processzorára nem minden pip package található meg (ha minden igaz akkor a dependenciák közül csak az _opencv-contrib_ problémás). Így ha ott szeretnénk, akkor ahhoz először le kell fordítani forráskódból a library-t, amit én természetesen meg is tettem, de mint már írtam, most nem javaslom, hiszen körülbelül ugyanúgy működik sima asztali gépről is.

Mivel a feltöltési méretkorlátokat túllépi a modellekkel együtt a szoftver inkább azt mutatnám be, hogy GitHub-ról letöltve, hogyan lehet elindítani a lehető leggyorsabban a szoftvert.

A tanításhoz készítettem arc adat szetteket is, de azokat a méret miatt nem töltöttem fel.

## Telepítés

### Klónozás és környezet beállítása

```bash
mt:mt MT\$ git clone https://github.com/MTTRK/RaspberryPi_Security.git
Cloning into 'RaspberryPi_Security'...
...
Resolving deltas: 100% (528/528), done.
mt:mt MT\$ python3 --version
Python 3.6.
mt:mt MT\$ pip3 --version
pip 9.0.3 from /usr/local/lib/python3.6/site-packages (python 3.6)
mt:mt MT\$ pip3 install virtualenv
Requirement already satisfied: virtualenv in /usr/local/lib/python3.6/site-packages
mt:mt MT\$ ls
RaspberryPi_Security
```

Látható, hogy sikeresen lehúztuk a repository-t. Ezenkívül rendelkezünk Python3-al (3.6.5) és pip3-al is, sőt feltelepítettük a virtualenv-et is.

### Pip packagek telepítése virtualenv használatával

```bash
mt:mt MT\$ cd RaspberryPi_Security/
mt:RaspberryPi_Security MT\$ ls
README.md config make.sh raspberry_sec requirements.txt
mt:RaspberryPi_Security MT\$ virtualenv rpi_env
Using base prefix '/usr/local/Cellar/python/3.6.5/Frameworks/Python.framework/Versions/3.6'
New python executable in /private/var/tmp/mt/RaspberryPi_Security/rpi_env/bin/python3.
Also creating executable in /private/var/tmp/mt/RaspberryPi_Security/rpi_env/bin/python
Installing setuptools, pip, wheel...done.
mt:RaspberryPi_Security MT\$ ls
README.md config make.sh raspberry_sec requirements.txt rpi_env
mt:RaspberryPi_Security MT\$ source rpi_env/bin/activate
(rpi_env) mt:RaspberryPi_Security MT\$ python --version
Python 3.6.
```

Mivel pip3-al telepítettük a virtualenv-et, azt használva Python3-at fogunk használni, de ez egyébként konfigurálható a `–p` kapcsolóval is (`virtualenv --help`).

```bash
(rpi_env) mt:RaspberryPi_Security MT\$ pip list
Package Version
---------- -------
pip 10.0.
setuptools 39.1.
wheel 0.31.
(rpi_env) mt:RaspberryPi_Security MT\$ pip install -r requirements.txt
Collecting opencv-python==3.3.0.10 (from -r requirements.txt (line 1))
Using cached
...
Installing collected packages: numpy, opencv-python, opencv-contrib-python, py, pytest,
tornado, scrypt, six, protobuf, werkzeug, tensorflow, pyyaml, scipy, keras, h5py, scikit-
learn, sklearn
Successfully installed h5py-2.7.1 keras-2.1.2 numpy-1.14.3 opencv-contrib-python-3.3.0.
opencv-python-3.3.0.10 protobuf-3.5.2.post1 py-1.5.3 pytest-3.2.2 pyyaml-3.12 scikit-learn-
0.19.1 scipy-1.1.0 scrypt-0.8.6 six-1.11.0 sklearn-0.0 tensorflow-1.1.0 tornado-4.5.
werkzeug-0.14.
(rpi_env) mt:RaspberryPi_Security MT\$ pip list
Package Version
--------------------- -----------
h5py 2.7.
Keras 2.1.
numpy 1.14.
opencv-contrib-python 3.3.0.
opencv-python 3.3.0.
pip 10.0.
protobuf 3.5.2.post
py 1.5.
pytest 3.2.
PyYAML 3.
scikit-learn 0.19.
scipy 1.1.
scrypt 0.8.
setuptools 39.1.
six 1.11.
sklearn 0.
tensorflow 1.1.
tornado 4.5.
Werkzeug 0.14.
wheel 0.31.
```

Látható, hogy sikeresen feltelepítettük pip-el a packageket.

### UI beállítása (SSL tanusítvány és Admin jelszó)

```bash
(rpi_env) mt:passwd MT\$ pwd
/var/tmp/mt/ RaspberryPi_Security/raspberry_sec/ui/resource/passwd
(rpi_env) mt:passwd MT\$ ls
setup_admin.py setup_admin.sh
(rpi_env) mt:passwd MT\$ sudo setup_admin.sh
Password:
Enter your password please:
Repeat it please:
(rpi_env) mt:passwd MT\$ ls
passwd setup_admin.py setup_admin.sh
(rpi_env) mt:passwd MT\$ cat passwd
...
```

Azért root-ként javasolt futtatni, mert akkor ő lesz a tulajdonos, és read jogokat adva csak olvasni lehet ezt a hash-t, de megváltoztatni semmiképp nem mert a service úgyse root-ként fog futni (és write joga másnak nincs). A UI itt fogja keresni a jelszó-fájlt szóval itt helyben futtassuk a scriptet, pont ahogy én tettem.

```bash
(rpi_env) mt:ssl MT\$ pwd
/var/tmp/mt/ RaspberryPi_Security/raspberry_sec/ui/resource/ssl
(rpi_env) mt:ssl MT\$ ls
setup_https.sh
(rpi_env) mt:ssl MT\$ sudo setup_https.sh
Password:
The IP address (domain name) I am creating the certificate for?
localhost
chmod: root\*: No such file or directory
chmod: server\*: No such file or directory
chmod: v3\*: No such file or directory
rm: root\*: No such file or directory
rm: server\*: No such file or directory
rm: v3\*: No such file or directory
Generating RSA private key, 2048 bit long modulus
....
Generating a 2048 bit RSA private key
...
writing new private key to 'server.key'
-----
Signature ok
subject=/C=HU/ST=Hungary/L=Budapest/O=PCA
Corp./OU=HomeSec/emailAddress=info@pca.com/CN=localhost
Getting CA Private Key
(rpi_env) mt:ssl MT\$ ls
rootCA.key rootCA.srl server.csr server.key v3.ext
rootCA.pem server.crt server.csr.config setup_https.sh
```

Amint látjuk, sikeresen létrejött a rootCA-nk és a szerverünk saját tanusítványa, amit SSL/TLS-re fog használni, hogy titkosított kommunikáció legyen a kliensek és a szerver között. Most _localhost_-ra készítettem a tanusítványt.

### NN Recognizer modul beállítása

GitHub méret korlátai miatt, csak két darabban tudtam feltölteni a fájlt (normális esetben ezt nem tenném meg, hiszen ez egy generálható modell, ráadásul saját használatra van, de a diplomaterv miatt, most nem szeretném a tesztelőt arra kényszeríteni, hogy saját modellt kelljen építenie egy gyors teszthez).

```bash
(rpi_env) mt:resources MT\$ pwd
/var/tmp/mt/ RaspberryPi_Security/raspberry_sec/module/nnrecognizer/resources
(rpi_env) mt:resources MT\$ ls
model.z01 model.zip
(rpi_env) mt:resources MT\$ cat \* > model_all.zip
(rpi_env) mt:resources MT\$ ls -l
total 405552
- rw-r--r-- 1 MT wheel 67108864 May 15 21:48 model.z
- rw-r--r-- 1 MT wheel 36709751 May 15 21:48 model.zip
- rw-r--r-- 1 MT wheel 103818615 May 15 22:19 model_all.zip
(rpi_env) mt:resources MT\$ unzip model_all.zip
Archive: model_all.zip
warning [model_all.zip]: zipfile claims to be last disk of a multi-part archive;
attempting to process anyway, assuming all parts have been concatenated
together in order. Expect "errors" and warnings...true multi-part support
doesnt exist yet (coming soon).
warning [model_all.zip]: 67108864 extra bytes at beginning or within zipfile
(attempting to process anyway)
file #1: bad zipfile offset (local header sig): 67108868
(attempting to re-compensate)
inflating: model.h5py
(rpi_env) mt:resources MT\$ ls
model.h5py model.z01 model.zip model_all.zip
```

Tehát a két partial zip-et egy nagy fájlba dumpoltam és aztán azt a nagy fájlt (model_all.zip) kitömörítettem.

## Szoftver elindítása

```bash
(rpi_env) mt:ui MT\$ pwd
/var/tmp/mt/ RaspberryPi_Security/raspberry_sec/ui
(rpi_env) mt:ui MT\$ python main.py
```

Egyelőre még nem látunk semmit, nyissunk egy böngészőt: <https://localhost:8080>

![Login screen](images/install-guide/login-screen.png)

Ha beütünk valami rossz jelszót a fenti vörös üzenet fogad minket, de ha az előbb beállított admin jelszót adjuk meg akkor belépünk és ezt a log is megerősíti.

```
[INFO]:[2018- 05 - 15 22:25:43,994]:[MainProcess,MainThread]:tornado.access - 302 GET / (::1) 1.40ms
[INFO]:[2018- 05 - 15 22:25:43,999]:[MainProcess,MainThread]:LoginHandler - Handling GET message
[INFO]:[2018- 05 - 15 22:25:44,005]:[MainProcess,MainThread]:tornado.access - 200 GET /login?next=%2F (::1) 7.41ms
[INFO]:[2018- 05 - 15 22:25:44,036]:[MainProcess,MainThread]:tornado.access - 200 GET
/static/css/dashboard.css?v=b7a77cf1c265dc18bd2d79ec06da2077 (::1) 10.34ms
[INFO]:[2018- 05 - 15 22:25:44,042]:[MainProcess,MainThread]:tornado.access - 200 GET
/static/css/login.css?v=09678ef2873700bc9a5eb234febb7b6e (::1) 1.27ms
[INFO]:[2018- 05 - 15 22:25:44,210]:[MainProcess,MainThread]:tornado.access - 200 GET
/static/js/app.js?v=9f2e6253e2023598898903509cc3f0aa (::1) 1.95ms
[INFO]:[2018- 05 - 15 22:25:44,237]:[MainProcess,MainThread]:tornado.access - 200 GET
/static/img/pilogo.png?v=e15c3995dd9a65699d7ab4bc60bbbbf8 (::1) 2.37ms
[INFO]:[2018- 05 - 15 22:25:44,586]:[MainProcess,MainThread]:tornado.access - 200 GET
/static/img/pca.png?v=db40c2effdfa19b778ab6297441a8ca5 (::1) 0.83ms
[INFO]:[2018- 05 - 15 22:27:58,340]:[MainProcess,MainThread]:LoginHandler - Handling POST message
[INFO]:[2018- 05 - 15 22:27:58,340]:[MainProcess,MainThread]:LoginHandler - Checking credentials
[INFO]:[2018- 05 - 15 22:27:58,441]:[MainProcess,MainThread]:tornado.access - 302 POST /login (::1) 101.57ms
[INFO]:[2018- 05 - 15 22:27:58,446]:[MainProcess,MainThread]:LoginHandler - Handling POST message
[INFO]:[2018- 05 - 15 22:27:58,446]:[MainProcess,MainThread]:LoginHandler - Checking credentials
[INFO]:[2018- 05 - 15 22:27:58,532]:[MainProcess,MainThread]:tornado.access - 302 POST /login?next=%2F (::1) 86.51ms
[INFO]:[2018- 05 - 15 22:27:58,536]:[MainProcess,MainThread]:MainHandler - Handling GET message
[INFO]:[2018- 05 - 15 22:27:58,538]:[MainProcess,MainThread]:tornado.access - 200 GET / (::1) 2.50ms
[INFO]:[2018- 05 - 15 22:27:58,543]:[MainProcess,MainThread]:MainHandler - Handling GET message
[INFO]:[2018- 05 - 15 22:27:58,544]:[MainProcess,MainThread]:tornado.access - 200 GET / (::1) 1.39ms
[INFO]:[2018- 05 - 15 22:27:58,569]:[MainProcess,MainThread]:tornado.access - 200 GET
/static/css/dashboard.css?v=b7a77cf1c265dc18bd2d79ec06da2077 (::1) 1.74ms
[INFO]:[2018- 05 - 15 22:27:58,579]:[MainProcess,MainThread]:tornado.access - 200 GET
/static/css/login.css?v=09678ef2873700bc9a5eb234febb7b6e (::1) 2.11ms
```

Talán a legjobb kis teszt ha elindítjuk a rendszert és megnézzük a kamera képet, valamint ha emailt is akarunk kapni, érdemes annak a modulnak is a konfigurációját módosítani:

![Configuration page](images/install-guide/config-page.png)

Látszik, hogy be tudjuk állítani kinek menjen az értesítés és azt is, hogy kitől (mt.raspberry.pi@google.com egy általunk létrehozott google-fiók, jelszó is van hozzá természetesen, de azt repository-ba nem kommitáltuk be, ezért se látható a jelenlegi konfigurációban).

Ha esetleg nem a 0-ik device lenne a kamera, akkor mindkét jelenleg bekonfigurált stream-nél azt még be kell állítani, így le kell görgetni az alábbi részekhez (két stream van, tehát két ilyen is van):

![Camera device id configuration](images/install-guide/config-camera-device-id.png)

Amint megvagyunk a módosítással, a Save gombra kattintva lementetthetjük a rendszerrel az új konfigurációt, amit a legközelebbi start-upnál fel fog olvasni.

Indítsuk el és nézzük meg a logot majd a kamera képét is:

![View camera image](images/install-guide/view-camera.png)

## Recognizer modulok tanítása

A tanításhez szükség van a megfelelő helyeken fotókra.

```bash
(rpi_env) mt:facerecognizer MT\$ pwd
/var/tmp/mt/ RaspberryPi_Security/raspberry_sec/module/facerecognizer
(rpi_env) mt:facerecognizer MT\$ ls
**init**.py **pycache** consumer.py resources test.py
(rpi_env) mt:facerecognizer MT\$ ls resources/
eigen.yml haarcascade_frontalface_default.xml lbph.yml
fisher.yml labels.json train
(rpi_env) mt:facerecognizer MT\$ ls resources/ train /
mate_c mate_f yalefaces
(rpi_env) mt:facerecognizer MT\$ python test.py -h
usage: test.py [-h][-p] [-w WHO][-tr]

== Face Recognizer (testing/training module) ==

optional arguments:
- h, --help show this help message and exit
- p, --produce If training data should be produced (no training/testing)
- w WHO, --who WHO For whom the data should be produced (only with -p)
- tr, --training If training should be conducted before testing
```

Most pedig futassuk `–tr` flag-el:

```bash
mt:facerecognizer MT\$ python test.py -tr
2018 - 05 - 15 23:02:44,725:FacedetectorConsumer:INFO - Initializing component
2018 - 05 - 15 23:02:44,810:FacedetectorConsumer:INFO - Face detected
2018 - 05 - 15 23:02:46,241:FacedetectorConsumer:DEBUG - Could not detect any faces
2018 - 05 - 15 23:02:46,250:FacedetectorConsumer:DEBUG - Could not detect any faces
2018 - 05 - 15 23:02:46,266:FacedetectorConsumer:DEBUG - Could not detect any faces
2018 - 05 - 15 23:02:46,283:FacedetectorConsumer:INFO - Face detected
...
```

Itt tulajdonképpen az történik, hogy a training előtt felolvassuk a képeket, pre-processzáljuk őket (size, color, face-detection, labelling) és utána továbbadjuk a training metódusoknak. Ezután elindul a tényleges testing is, ami mint már a dolgozatban rámutattam, egészen manuális (kamerakép mutatja aktuális detectált arcot és az ID-t akivel azonosította).

Most nézzük meg hasonlóképpen a neurális háló modul training/test-jét:

```bash
(rpi_env) mt:nnrecognizer MT\$ pwd
/var/tmp/mt/RaspberryPi_Security/raspberry_sec/module/nnrecognizer
(rpi_env) mt:nnrecognizer MT\$ ls resources/
model.h5py model.z01 model.zip model_all.zip train
(rpi_env) mt:nnrecognizer MT\$ ls resources/train/
neg pos
(rpi_env) mt:nnrecognizer MT\$ python test.py -h

/private/var/tmp/mt/RaspberryPi_Security/rpi_env/lib/python3.6/site-packages/h5py/**init**.py:36: FutureWarning:
Conversion of the second argument of issubdtype from `float` to `np.floating` is deprecated. In future, it will
be treated as `np.float64 == np.dtype(float).type`.
from .\_conv import register_converters as \_register_converters
Using TensorFlow backend.
usage: test.py [-h][-tr] [-d][-u]

== NN Face Recognizer (testing/training module) ==

optional arguments:
- h, --help show this help message and exit
- tr, --training If training should be conducted before testing
- d, --detect If the input should go under face-detection (only with -tr)
- u, --update If the input should be updated with the face that has been detected (only with -d)
```

Ott van a két mintahalmaz. Most pedig indítsuk el a training-elést.

A `–d` és `–u` kapcsolók a pre-processzinghez tartoznak.

Ezek lényegében azt a célt szolgálják, hogy ha pl. egy teljes alakos embert képet akarunk felhasználni akkor ahhoz először mindenképp arcot kell detektáljunk és utána mentsük is természetesen le az "új" képet. Nos a kapcsolók ennek irányítására szolgálnak. Én most tehát nem fogom őket használni és csak simán a `–tr` flag-el fogom futtatni a programot (lassú folyamat, hiszen kb. 6000 kép minta van és hát egy neurális háló is, szóval maximum ha GPU is áll rendelkezésre, tensorflow backend telepítve van packagek között):

```bash
(rpi_env) mt:nnrecognizer MT\$ python test.py -tr
/private/var/tmp/mt/RaspberryPi_Security/rpi_env/lib/python3.6/site-
packages/h5py/**init**.py:36: FutureWarning: Conversion of the second argument of issubdtype
from `float` to `np.floating` is deprecated. In future, it will be treated as `np.float64 ==
np.dtype(float).type`.
from .\_conv import register_converters as \_register_converters
Using TensorFlow backend.
Class: 0 --> resources/train/neg
Class: 1 --> resources/train/pos

...
Total params: 9,275,
Trainable params: 9,275,
Non-trainable params: 0

Train on 4796 samples, validate on 1599 samples

#192/4796 [>.............................] - ETA: 25:52 - loss: 0.4043 - acc: 0.
...
```
