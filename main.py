import hashlib
import json
import pyfiglet
import os
import random
import string
import sqlite3
from getpass import getpass
from termcolor import colored


class PasswordManager:
    def __init__(self):
        self.title = pyfiglet.figlet_format("Password Manager") # PASSWORD MANAGER
        print(colored(self.title, "cyan"))
        self.folder_name = "PMExported" 
        self.directory = os.path.dirname(os.path.abspath(__file__))
        self.default_path = os.path.join(self.directory, self.folder_name)

        if not os.path.exists(self.default_path):
            os.makedirs(self.default_path)

        self.user = str()
        self.create_database()
    
    def create_database(self):
        self.database_path = self.default_path + f"\PM.db"
        self.database = sqlite3.connect(self.database_path)
        self.cur = self.database.cursor()

    def signup(self):
        print(colored("\nCreate a username and password:", "cyan"))
        signup_username = input(colored("Username: $ ", "yellow")).strip()
        signup_password = getpass(colored("Password: $ ", "yellow"))
        signup_password = hashlib.sha256(signup_password.encode()).hexdigest()
        signup_user_info = (signup_username, signup_password)

        # Check if username available
        self.cur.execute("SELECT username FROM Users WHERE username = ?", (signup_username,))
        self.database.commit()
        fetching_result = self.cur.fetchall()

        if len(fetching_result) > 0:
            print("User already exists!")
            while True:
                option = input("(L)ogin\n(C)hange Username\n(Q)uit:\n$ ").strip().lower()
                if option == "c":
                    self.signup()
                    break
                elif option == "l":
                    self.login()
                    break
                elif option == "q":
                    quit()
                else:
                    print("Choose only from the options below: ")
        else:
            self.cur.execute("INSERT INTO Users VALUES(?, ?)", signup_user_info)
            self.database.commit()
            self.user = signup_username 

        
    def login(self):
        print(colored("\nLogin with your username and password:", "cyan"))
        login_username = input(colored("Username: $ ", "yellow")).strip()
        login_password = getpass(colored("Password: $ ", "yellow"))
        login_password = hashlib.sha256(login_password.encode()).hexdigest()
        login_user_info = (login_username, login_password)

        # Check if user is already in database
        self.cur.execute("SELECT username FROM Users WHERE username = ? and password = ?", login_user_info)
        self.database.commit()
        fetching_result = self.cur.fetchone()

        if fetching_result is None:
            print("Login Info are incorrect or user does not exist.\n")
            while True:
                option = input("(S)ign Up\n(R)etry\n(Q)uit:\n$ ").strip().lower()
                if option == "s":
                    self.signup()
                    break
                elif option == "r":
                    self.login()
                    break
                elif option == "q":
                    quit()
                else:
                    print("Choose only one from the options below: ")
        else:
            self.user = login_username

    def user_info(self):
        self.cur.execute("CREATE TABLE IF NOT EXISTS Users (username TEXT, password TEXT)")
        self.database.commit()
        while True:
            option = input("(L)ogin or (S)ign Up: $ ").strip().lower()
            if option == "s":
                self.signup()
                break
            elif option == "l":
                self.login()
                break
            else:
                print("Choose only from the options below: ")

    def options(self):
        text = "\nChoose one from the options below:\n(G)enerate a new password.\n(E)xport all passwords.\n(U)pdate password.\n(R)emove password.\n(C)hange User\n(Q)uit.\n"
        option = input(text + "\n$ ").strip().lower()
        while True:
            if option == "g":
                self.generate_password()
                break
            elif option == "e":
                self.export_passwords()
                break
            elif option == "u":
                self.update_password()
                break
            elif option == "r":
                self.remove_password()
                break
            elif option == "c":
                self.change_user()
                break
            elif option == "q":
                quit()
            else:
                print("Invalid Input")
    
    def randomize_password(self):
        characters = string.ascii_letters + string.digits + string.punctuation
        lst = []
        for _ in range(14):
            lst.append(characters[random.randint(0, len(characters) - 1)])
        random_password = "".join(lst)
        return random_password

    def generate_password(self):
        website_name = input("Website name: $ ").strip()
        email = input("Account email or username: $ ").strip()
        url = input("Website URL: $ ").strip()
        password = self.randomize_password()

        # Creating table for the user if it does not exist
        self.cur.execute("CREATE TABLE IF NOT EXISTS PM (website_name TEXT, email TEXT, url TEXT, password TEXT, user TEXT)")
        self.database.commit()
        print(f"The generated password is", colored(password, "yellow"))

        # Adding Infos to database
        self.cur.execute(f"INSERT INTO PM (website_name, email, url, password, user) VALUES(?, ?, ?, ?, ?)", (website_name, email, url, password, self.user))
        self.database.commit()
        self.options()

    def export_passwords(self):
        self.cur.execute(f"SELECT website_name, email, url, password FROM PM WHERE user = ?", (self.user,))
        user_passwords = self.cur.fetchall()
        user_json = []

        for password in user_passwords:
            website_name, email, url, password_text = password
            user_json.append({
                "Website Name": website_name,
                "Email or Username": email,
                "URL": url,
                "Password": str(password_text)
            })

        json_filename = f"{self.user}.json"
        json_path = os.path.join(self.default_path, json_filename)

        with open(json_path, "w") as json_file:
            json.dump(user_json, json_file, indent=4)

        print(colored(f"Exported to {json_path} successfully. Make sure to save the file in a secure location because it is not encrypted.", "green"))
        self.options()

    def update_password(self):
        website_name = input("Website Name: $ ").strip()
        password = input("Set New Password: $ ")
        self.cur.execute(f"UPDATE PM SET password = '{password}' WHERE website_name = '{website_name}' and user = '{self.user}'")
        rows = self.cur.rowcount
        if rows == 0:
            print("No such data.")
            while True:
                option = input("(R)eenter Website Name\n(Q)uit:\n$ ").strip().lower()
                if option == "r":
                    self.update_password()
                    break
                elif option == "q":
                    quit()
                else:
                    print("Choose only from the options below: ")
        else:          
            print("Password updated")
        self.database.commit()
        self.options()

    def remove_password(self):
        website_name = input("Website Name: $ ").strip()
        self.cur.execute(f"DELETE FROM PM WHERE website_name = ? and user = ?", (website_name, self.user))
        rows = self.cur.rowcount
        if rows == 0:
            print("No such data.")
            while True:
                option = input("(R)eenter Website Name\n(Q)uit:\n$ ").strip().lower()
                if option == "r":
                    self.remove_password()
                    break
                elif option == "q":
                    quit()
                else:
                    print("Choose only from the options below: ")
        else:
            print("Saved password deleted.")
        self.database.commit()
        self.options()

    def change_user(self):
        self.user_info()

    def run(self):
        self.user_info()
        self.options()
        self.database.close()


if __name__ == "__main__":
    main = PasswordManager()
    main.run()