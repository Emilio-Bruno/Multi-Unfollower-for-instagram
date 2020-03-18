from PyQt5 import QtWidgets, uic, QtCore, QtGui
import string
import random
import requests
import shutil
import json
import sys
import os
import time
import urllib.request


class Login(QtWidgets.QMainWindow):
    def __init__(self):

        self.session = requests.Session()

        lettersAndDigits = string.ascii_letters + string.digits
        self.headers = {
            "Host": "www.instagram.com",
            "User-Agent": "Mozilla/5.0 (Macintosh Intel Mac OS X 10.13 rv: 73.0) Gecko/20100101 Firefox/73.0",
            "Accept-Language": "en-US, en",
            "X-CSRFToken": "".join(random.choice(lettersAndDigits) for i in range(32)),
        }

        try:
            dataFile = open("data.json", "r")
            data = json.loads(dataFile.read())
            username = data["username"]
            password = data["password"]
            dataFile.close()

            result = self.login(username, password)

            if result != "success":
                print(result)
            else:
                self.window = Main(username, password, self.headers, self.session)

        except:
            super(Login, self).__init__()
            uic.loadUi("login.ui", self)
            self.setWindowFlags(
                QtCore.Qt.WindowCloseButtonHint | QtCore.Qt.WindowMinimizeButtonHint
            )
            self.loginBtn.clicked.connect(self.loginBtn_pressed)
            self.result.hide()
            self.show()

    def loginBtn_pressed(self):
        username = self.username.text()
        password = self.password.text()
        self.result.show()

        result = self.login(username, password)

        if result != "success":
            self.result.setText(result)
        else:
            self.window = Main(username, password, self.headers, self.session)
            self.hide()

    def login(self, username, password):
        if len(password) < 6:
            dataFile = open("data.json", "w")
            dataFile.close()
            return "Password is too short"

        url = "https://www.instagram.com/accounts/login/ajax/"
        data = {"username": username, "password": password}

        response = self.session.post(url, data=data, headers=self.headers)

        try:
            if response.json()["authenticated"] == False:
                dataFile = open("data.json", "w")
                dataFile.close()
                return "Wrong login data"
        except:
            return "Error occured during the post request"

        dataFile = open("data.json", "w")
        print(json.dumps(data), file=dataFile)
        dataFile.close()

        self.headers["X-CSRFToken"] = self.session.cookies["csrftoken"]
        return "success"


class Main(QtWidgets.QMainWindow):
    def __init__(self, username, password, headers, session):
        super(Main, self).__init__()
        uic.loadUi("main.ui", self)
        self.setWindowFlags(
            QtCore.Qt.WindowCloseButtonHint | QtCore.Qt.WindowMinimizeButtonHint
        )
        self.headers = headers
        self.session = session
        self.logoutBtn.clicked.connect(self.logoutBtn_pressed)
        self.reloadBtn.clicked.connect(self.reloadBtn_pressed)
        self.flag = False
        self.j = 0
        self.id = {}
        self.username = {}
        self.openFollowing()
        self.tableFollower.resizeColumnsToContents()
        self.show()

    def logoutBtn_pressed(self):
        url = "https://www.instagram.com/accounts/logout/"

        data = {"csrfmiddlewaretoken": self.session.cookies["csrftoken"]}

        response = self.session.post(url, headers=self.headers, data=data)
        if response.status_code != 200:
            print("Error occured during the post request")
            self.close()

        dataFile = open("data.json", "w")
        dataFile.close()
        self.close()

    def reloadBtn_pressed(self):
        self.tableFollower.setRowCount(0)
        shutil.rmtree("images/", ignore_errors=True)
        os.mkdir("images")
        self.flag = True
        self.j = 0
        self.id = {}
        self.username = {}
        self.openFollowing()

    def openFollowing(self):
        self.loadMoreBtn.show()

        url = (
            "https://www.instagram.com/graphql/query/?query_hash=d04b0a864b4b54837c0d870b0e77e076&variables=%7B%22id%22%3A%22"
            + self.session.cookies["ds_user_id"]
            + "%22%2C%22include_reel%22%3Afalse%2C%22fetch_mutual%22%3Afalse%2C%22first%22%3A10%7D"
        )

        self.response = self.session.get(url, headers=self.headers)
        if self.response.status_code != 200:
            print("Error occured during the get request")
            self.close()

        for i in self.response.json()["data"]["user"]["edge_follow"]["edges"]:
            image_url = i["node"]["profile_pic_url"]
            img_response = self.session.get(image_url, stream=True)

            image_url = "images/" + str(self.j) + ".jpeg"

            if img_response.status_code == 200:
                with open(image_url, "wb") as f:
                    img_response.raw.decode_content = True
                    shutil.copyfileobj(img_response.raw, f)
            else:
                print("error downloading the image")
                self.close()

            usernameLabel = QtWidgets.QLabel()
            fullNameLabel = QtWidgets.QLabel()
            userImage = QtWidgets.QLabel()
            checkbox = QtWidgets.QCheckBox()
            profileUrlLabel = QtWidgets.QLabel()
            verticalContainer = QtWidgets.QVBoxLayout()

            userImage.resize(50, 50)
            usernameLabel.setText(i["node"]["username"])
            fullNameLabel.setText(i["node"]["full_name"])
            profileUrl = (
                '<a href="https://www.instagram.com/'
                + i["node"]["username"]
                + '">Open Profile</a>'
            )
            profileUrlLabel.setText(profileUrl)
            profileUrlLabel.setAlignment(QtCore.Qt.AlignCenter)

            verticalContainer.addWidget(usernameLabel)
            verticalContainer.addWidget(fullNameLabel)
            userImage.setPixmap(QtGui.QPixmap(image_url).scaled(userImage.size()))
            profileUrlLabel.setOpenExternalLinks(True)

            verticalContainerWidget = QtWidgets.QWidget()
            verticalContainerWidget.setLayout(verticalContainer)

            rowsCount = self.tableFollower.rowCount()
            self.tableFollower.insertRow(rowsCount)

            self.tableFollower.setCellWidget(rowsCount, 0, checkbox)
            self.tableFollower.setCellWidget(rowsCount, 1, userImage)
            self.tableFollower.setCellWidget(rowsCount, 2, verticalContainerWidget)
            self.tableFollower.setCellWidget(rowsCount, 3, profileUrlLabel)
            self.username[str(self.j)] = i["node"]["username"]
            self.id[str(self.j)] = i["node"]["id"]
            self.j = self.j + 1

        if (
            self.response.json()["data"]["user"]["edge_follow"]["page_info"][
                "has_next_page"
            ]
            == True
        ):
            if self.flag == False:
                self.loadMoreBtn.clicked.connect(self.scrollFollowing)
        else:
            self.loadMoreBtn.hide()

        if self.flag == False:
            self.errorCount = 0
            self.unfollowBtn.clicked.connect(self.unfollowCheck)

    def scrollFollowing(self):
        if (
            self.response.json()["data"]["user"]["edge_follow"]["page_info"][
                "has_next_page"
            ]
            == True
        ):
            url = (
                "https://www.instagram.com/graphql/query/?query_hash=d04b0a864b4b54837c0d870b0e77e076&variables=%7B%22id%22%3A%22"
                + self.session.cookies["ds_user_id"]
                + "%22%2C%22include_reel%22%3Afalse%2C%22fetch_mutual%22%3Afalse%2C%22first%22%3A10%2C%22after%22%3A%22"
                + self.response.json()["data"]["user"]["edge_follow"]["page_info"][
                    "end_cursor"
                ][:-2]
                + "%3D%3D%22%7D"
            )

            self.response = self.session.get(url, headers=self.headers)

            try:
                for i in self.response.json()["data"]["user"]["edge_follow"]["edges"]:
                    image_url = i["node"]["profile_pic_url"]
                    img_response = self.session.get(image_url, stream=True)

                    image_url = "images/" + str(self.j) + ".jpeg"

                    if img_response.status_code == 200:
                        with open(image_url, "wb") as f:
                            img_response.raw.decode_content = True
                            shutil.copyfileobj(img_response.raw, f)
                    else:
                        print("error downloading the image")
                        self.close()

                    usernameLabel = QtWidgets.QLabel()
                    fullNameLabel = QtWidgets.QLabel()
                    userImage = QtWidgets.QLabel()
                    checkbox = QtWidgets.QCheckBox()
                    profileUrlLabel = QtWidgets.QLabel()
                    verticalContainer = QtWidgets.QVBoxLayout()

                    userImage.resize(50, 50)
                    usernameLabel.setText(i["node"]["username"])
                    fullNameLabel.setText(i["node"]["full_name"])
                    profileUrl = (
                        '<a href="https://www.instagram.com/'
                        + i["node"]["username"]
                        + '">Open Profile</a>'
                    )
                    profileUrlLabel.setText(profileUrl)
                    profileUrlLabel.setAlignment(QtCore.Qt.AlignCenter)

                    verticalContainer.addWidget(usernameLabel)
                    verticalContainer.addWidget(fullNameLabel)
                    userImage.setPixmap(
                        QtGui.QPixmap(image_url).scaled(userImage.size())
                    )
                    profileUrlLabel.setOpenExternalLinks(True)

                    verticalContainerWidget = QtWidgets.QWidget()
                    verticalContainerWidget.setLayout(verticalContainer)

                    rowsCount = self.tableFollower.rowCount()
                    self.tableFollower.insertRow(rowsCount)

                    self.tableFollower.setCellWidget(rowsCount, 0, checkbox)
                    self.tableFollower.setCellWidget(rowsCount, 1, userImage)
                    self.tableFollower.setCellWidget(
                        rowsCount, 2, verticalContainerWidget
                    )
                    self.tableFollower.setCellWidget(rowsCount, 3, profileUrlLabel)
                    self.username[str(self.j)] = i["node"]["username"]
                    self.id[str(self.j)] = i["node"]["id"]
                    self.j = self.j + 1
            except:
                print("Error occured during the get request")
                self.close()
        else:
            self.loadMoreBtn.hide()

    def unfollowCheck(self):
        self.time = self.doubleSpinBox.value() * 60
        for i in range(self.tableFollower.rowCount()):
            if self.tableFollower.cellWidget(i, 0).isChecked():
                self.unfollow(self.id[str(i)], self.username[str(i)])
                if self.tableFollower.rowCount() != i:
                    time.sleep(self.time)

    def unfollow(self, unfollowId, unfollowUser):
        if self.errorCount < 5:

            url = (
                "https://www.instagram.com/web/friendships/"
                + str(unfollowId)
                + "/unfollow/"
            )

            response = self.session.post(url, headers=self.headers)

            if response.status_code != 200:
                print("Error occured during the post request")
                self.errorCount = self.errorCount + 1
            else:
                print(unfollowUser + " unfollowed")
        else:
            print("Error occured during the post request")
            self.close()
