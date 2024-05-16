import os
import requests
import base64
import json
from colorama import init, Fore, Style

init(autoreset=True)  # Initialize colorama for colored output


def clear_screen():
    os.system('cls' if os.name == 'nt' else 'clear')


def display_logo():
    print(Fore.CYAN + Style.BRIGHT + """
     _   __      _  __
    / | / /___  (_)/ /_
   /  |/ / __ \/ / / __/
  / /|  / /_/ / / / /_
 /_/ |_/ .___/_/ /\__\
      /_/
    """)


def get_token():
    try:
        with open('.token.json', 'r') as f:
            data = json.load(f)
            return data.get('token')
    except FileNotFoundError:
        token = input(Fore.YELLOW + "Enter your GitHub token: " + Style.RESET_ALL)
        save_token(token)
        return token


def save_token(token):
    with open('.token.json', 'w') as f:
        json.dump({'token': token}, f)


def delete_token():
    try:
        os.remove('.token.json')
        print(Fore.GREEN + "Token deleted successfully." + Style.RESET_ALL)
    except FileNotFoundError:
        print(Fore.YELLOW + "No token file found." + Style.RESET_ALL)


class GitHubAPI:
    def __init__(self, token):
        self.token = token
        self.headers = {
            'Authorization': f'token {token}',
            'Accept': 'application/vnd.github.v3+json'
        }
        self.base_url = 'https://api.github.com'

    def create_repo(self, repo_name, description="", add_readme=False):
        url = f'{self.base_url}/user/repos'
        data = {'name': repo_name, 'description': description, 'auto_init': add_readme}
        response = requests.post(url, headers=self.headers, json=data)
        return response.json()

    def delete_repo(self, repo_names):
        success = []
        for repo_name in repo_names:
            url = f'{self.base_url}/repos/{repo_name}'
            response = requests.delete(url, headers=self.headers)
            if response.status_code == 204:
                success.append(repo_name)
        return success

    def add_file(self, owner, repo_name, file_name, file_content):
        url = f'{self.base_url}/repos/{owner}/{repo_name}/contents/{file_name}'
        data = {
            'message': 'Add new file',
            'content': file_content
        }
        response = requests.put(url, headers=self.headers, json=data)
        return response.status_code == 201

    def add_folder(self, owner, repo_name, folder_path):
        self.upload_folder(owner, repo_name, folder_path)
        print(Fore.GREEN + "Folder added successfully." + Style.RESET_ALL)

    def upload_folder(self, owner, repo_name, folder_path):
        print(Fore.CYAN + f"Uploading folder {folder_path} to repository {repo_name}..." + Style.RESET_ALL)
        url = f"https://api.github.com/repos/{owner}/{repo_name}/contents/"
        headers = {
            "Authorization": f"token {self.token}",
            "Accept": "application/vnd.github.v3+json"
        }
        for root, _, files in os.walk(folder_path):
            for file_name in files:
                file_path = os.path.join(root, file_name)
                with open(file_path, "rb") as file:
                    file_content = file.read()
                file_content_encoded = base64.b64encode(file_content).decode()
                relative_path = os.path.relpath(file_path, folder_path)
                payload = {
                    "message": f"Upload {relative_path}",
                    "content": file_content_encoded,
                    "branch": "main"
                }
                response = requests.put(url + relative_path, headers=headers, json=payload)
                if response.status_code == 201:
                    print(Fore.GREEN + f"File '{relative_path}' uploaded successfully." + Style.RESET_ALL)
                else:
                    print(Fore.RED + f"Failed to upload file '{relative_path}'. Error: {response.json().get('message', '')}" + Style.RESET_ALL)

    def get_user_repos(self, username):
        url = f'{self.base_url}/users/{username}/repos'
        response = requests.get(url, headers=self.headers)
        return response.json()

    def view_repo_contents(self, owner, repo_name):
        url = f'{self.base_url}/repos/{owner}/{repo_name}/contents'
        response = requests.get(url, headers=self.headers)
        contents = response.json()
        for item in contents:
            print(item['name'])

    def download_repo_contents(self, owner, repo_name, path):
        url = f'{self.base_url}/repos/{owner}/{repo_name}/contents'
        response = requests.get(url, headers=self.headers)
        contents = response.json()
        for item in contents:
            if item['type'] == 'file':
                content_url = item['download_url']
                file_content = requests.get(content_url, headers=self.headers).text
                with open(f'{path}/{item["name"]}', 'w') as f:
                    f.write(file_content)


if __name__ == "__main__":
    clear_screen()
    display_logo()

    token = get_token()
    github_api = GitHubAPI(token)

    while True:
        clear_screen()
        print(Fore.BLUE + Style.BRIGHT + " " + "_" * 40 + " " + Style.RESET_ALL)
        print(Fore.CYAN + Style.BRIGHT + " " + "GitHub CLI" + " " * 15 + Style.RESET_ALL)
        print(Fore.BLUE + Style.BRIGHT + " " + "_" * 40 + " " + Style.RESET_ALL)
        print("1. Create Repo")
        print("2. Delete Repo")
        print("3. Add Folder")
        print("4. View Another User Repo")
        print("5. Download Code from your repo/other repo")
        print("6. Delete Token")
        print("7. Exit")

        choice = input(Fore.YELLOW + "Enter your choice: " + Style.RESET_ALL)

        if choice == "1":
            clear_screen()
            repo_name = input("Enter repository name: ")
            description = input("Enter repository description: ")
            add_readme = input("Do you want to add a readme file (y/n): ").lower() == 'y'
            new_repo = github_api.create_repo(repo_name, description, add_readme)
            print(Fore.GREEN + "Repository created:", new_repo.get('html_url', '') + Style.RESET_ALL)

        elif choice == "2":
            clear_screen()
            username = input("Enter your GitHub username: ")
            user_repos = github_api.get_user_repos(username)
            for i, repo in enumerate(user_repos, 1):
                print(f"{i}. {repo['name']}")
            to_delete = input("Enter the number(s) of the repository to delete (use ',' to separate multiple numbers): ")
            repos_to_delete = [user_repos[int(i) - 1]['full_name'] for i in to_delete.split(',')]
            deleted_repos = github_api.delete_repo(repos_to_delete)
            print(Fore.GREEN + "Deleted repositories:", deleted_repos + Style.RESET_ALL)

        elif choice == "3":
            clear_screen()
            username = input("Enter your GitHub username: ")
            user_repos = github_api.get_user_repos(username)
            for i, repo in enumerate(user_repos, 1):
                print(f"{i}. {repo['name']}")
            repo_num = int(input("Enter the repository number to add folder: "))
            repo_name = user_repos[repo_num - 1]['name']
            folder_path = input("Enter the folder location: ")
            github_api.add_folder(username, repo_name, folder_path)

        elif choice == "4":
            clear_screen()
            username = input("Enter username: ")
            user_repos = github_api.get_user_repos(username)
            for i, repo in enumerate(user_repos, 1):
                print(f"{i}. {repo['name']}")
            repo_num = int(input("Enter the repository number to view files inside: "))
            repo_name = user_repos[repo_num - 1]['name']
            github_api.view_repo_contents(username, repo_name)

        elif choice == "5":
            clear_screen()
            username = input("Enter username: ")
            user_repos = github_api.get_user_repos(username)
            for i, repo in enumerate(user_repos, 1):
                print(f"{i}. {repo['name']}")
            repo_num = int(input("Enter the repository number to download: "))
            repo_name = user_repos[repo_num - 1]['name']
            download_path = input("Enter download path: ")
            github_api.download_repo_contents(username, repo_name, download_path)
            print(Fore.GREEN + "Code downloaded successfully." + Style.RESET_ALL)

        elif choice == "6":
            clear_screen()
            delete_token()

        elif choice == "7":
            clear_screen()
            print(Fore.CYAN + Style.BRIGHT + "Exiting program..." + Style.RESET_ALL)
            break

        else:
            clear_screen()
            print(Fore.RED + "Invalid choice. Please try again." + Style.RESET_ALL)
