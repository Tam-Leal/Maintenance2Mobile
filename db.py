import pyrebase
import random
import pandas as pd


class LogData:
    def __init__(self):
        self.dicio_issues = None
        self.total_reports = None

        self.config = {
            "apiKey": " your project api key ",
            "authDomain": " your project authDomain ",
            "databaseURL": " your project databaseURL ",
            "storageBucket": " your project storageBucket "
        }
        self.firebase = pyrebase.initialize_app(self.config)
        self.auth = self.firebase.auth()

    def create_user(self, user_email, user_password):
        # Create user
        self.auth.create_user_with_email_and_password(user_email, user_password)

    def set_profile(self, name, sector, user_email, user_password):
        # Sign in user
        user = self.auth.sign_in_with_email_and_password(user_email, user_password)

        # UID logged user
        uid = self.auth.current_user['localId']

        # Get a reference to the database service
        db = self.firebase.database()

        # # data to save
        data = {
            "name": name, "sector": sector
        }

        db.child("users").child(uid).child('profile').set(data=data, token=user['idToken'])

    def admin_profile(self, email, password):
        user = self.auth.sign_in_with_email_and_password(email, password)

        # Get a reference to the database service
        db = self.firebase.database()

        # Get the token from de admin set in realtime database
        db.child("admin").get(token=user['idToken'])

        return user['email']

    def logsession(self, user_email, user_password):
        # Sign in user
        user = self.auth.sign_in_with_email_and_password(user_email, user_password)

        # UID logged user
        uid = self.auth.current_user['localId']

        # Get a reference to the database service
        db = self.firebase.database()

        # Pass the user's idToken to the push method
        results = db.child("users").child(uid).child('profile').child('name').get(token=user['idToken'])

        return results.val()

    def load_profile(self, user_email, user_password):
        user = self.auth.sign_in_with_email_and_password(user_email, user_password)

        # UID logged user
        uid = self.auth.current_user['localId']

        # Get a reference to the database service
        db = self.firebase.database()

        # Get departament
        departament = db.child("users").child(uid).child('profile').child('sector').get(
            token=user['idToken']).val()

        return departament

    def load_issues(self, user_email, user_password):
        # Sign in user
        user = self.auth.sign_in_with_email_and_password(user_email, user_password)

        # Get a reference to the database service
        db = self.firebase.database()

        # List for issues
        list_issues = []
        issues = db.child("issues").get(token=user['idToken'])
        for user in issues.each():
            list_issues.append(user.val()['part'])

        return list_issues

    def requests(self, name, issue_select, description, time, dep, id_req, user_email, user_password):
        # Sign in user
        user = self.auth.sign_in_with_email_and_password(user_email, user_password)

        # Get a reference to the database service
        db = self.firebase.database()

        # Data to save
        data = {
            "name": name, "issue": issue_select, "description": description, "department": dep, "time": time,
            'id_req': id_req
        }

        db.child('requests').child(id_req).set(data=data, token=user['idToken'])

        # save to historic requests
        db.child('requests_historic').child(id_req).set(data=data, token=user['idToken'])

    def queue(self, user_email, user_password):
        user = self.auth.sign_in_with_email_and_password(user_email, user_password)

        # Get a reference to the database service
        db = self.firebase.database()

        # List for requests
        list_requests = []

        issues = db.child('requests').get(token=user['idToken'])
        if issues.each() is None:
            return ''
        else:
            for user in issues.each():
                list_requests.append(user.val())
            print(list_requests)
            return list_requests

    def save_issues(self, user_email, user_password, part):
        user = self.auth.sign_in_with_email_and_password(user_email, user_password)
        id_number = random.randrange(1, 1000, 3)

        # Get a reference to the database service
        db = self.firebase.database()

        # Data to save
        data = {
            "id": id_number, "part": part,
        }

        db.child('issues').push(data=data, token=user['idToken'])

    def remove_request(self, user_email, user_password, id_req):
        user = self.auth.sign_in_with_email_and_password(user_email, user_password)
        # Get a reference to the database service
        db = self.firebase.database()
        # Delete from database the request done
        db.child('requests').child(id_req).remove(token=user['idToken'])

    def stat_requests(self, user_email, user_password):
        user = self.auth.sign_in_with_email_and_password(user_email, user_password)

        # Get a reference to the database service
        db = self.firebase.database()

        # historic of requests
        historic_requests = []
        issues = db.child('requests_historic').get(token=user['idToken'])
        for user in issues.each():
            historic_requests.append(user.val())

        # Dataframe
        df = pd.DataFrame(historic_requests, columns=['issue'])

        for i in df['issue'].unique():
            df.loc[df['issue'] == i, 'qty'] = 1
        # New dataframe
        new_df = df.groupby(["issue"], as_index=False).sum()

        list_issues = new_df['issue'].values

        new_df['%'] = 100 * new_df['qty'] / new_df['qty'].sum()
        new_df['%'] = new_df['%'].round(decimals=4).astype(float)

        new_df['Cumulative %'] = new_df['%'].cumsum()

        new_df['Rounded'] = new_df['Cumulative %'].round(decimals=0).astype(float)

        new_df['Prev Base'] = new_df['Cumulative %'].diff().round(decimals=0).astype(float)
        new_df['Prev Base'] = new_df['Rounded'].diff().fillna(new_df['Rounded']).round(decimals=0).astype(object)

        list_count = list(new_df['Prev Base'].values)

        print(f'lista final: {list_count}')
        print(f'soma percentual da lista final: {sum(list_count)}')
        self.dicio_issues = [dict(zip(list_issues, list_count))]
        self.total_reports = new_df['qty'].sum().round(decimals=0).astype(int)
        print(self.dicio_issues)
        return self.dicio_issues, self.total_reports
