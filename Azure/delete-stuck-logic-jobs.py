import subprocess
import requests

# Set your Azure parameters
subscription_id = ""
resource_group_name = ""
workflow_name = ""
filter = "Status eq 'Running'"
api_version = "2016-06-01"

def get_authorization_token():
    try:
        # Run Azure CLI commands to authenticate and get the access token
        access_token = subprocess.check_output(["az", "account", "get-access-token", "--query", "accessToken", "-o", "tsv"]).decode().strip()
        print("Retrieved access token")
        return access_token
    except subprocess.CalledProcessError as e:
        print("Error executing Azure CLI commands:", e)
        subprocess.run(["az", "login"])
        get_authorization_token()
        return None

def get_runs(authorization_token):
    workflow_ids = []
    url = f"https://management.azure.com/subscriptions/{subscription_id}/resourceGroups/{resource_group_name}/providers/Microsoft.Logic/workflows/{workflow_name}/runs?api-version={api_version}&$filter={filter}"
    headers = {
        "Authorization": f"Bearer {authorization_token}"
    }
    count = 0
    while url:
        response = requests.get(url, headers=headers)
        if response.status_code == 200:
            data = response.json()
            runs = data.get('value', [])
            for run in runs:
                run_name = run.get('name')
                workflow_ids.append(run_name)
            next_link = data.get('nextLink')
            url = next_link if next_link else None
            count=(count + 1)
            print(f"Retrieved workflow runs: {next_link} Page {count}")
        else:
            print("Failed to retrieve runs:", response.status_code)
            return []
    return workflow_ids


def delete_run(run_name, authorization_token):
    url = f"https://management.azure.com/subscriptions/{subscription_id}/resourceGroups/{resource_group_name}/providers/Microsoft.Logic/workflows/{workflow_name}/runs/{run_name}?api-version={api_version}"
    headers = {
        "Authorization": f"Bearer {authorization_token}"
    }
    response = requests.delete(url, headers=headers)
    if response.status_code == 200:
        print(f"Successfully deleted run {run_name}")
    elif "because it is not in a terminal state" in response.json().get('error').get('message'):
        print(f"Failed to delete run {run_name}: {response.json().get('error').get('message')}")
        cancel_run(run_name, authorization_token)
        delete_run(run_name, authorization_token)
    else:
        print(f"Failed to delete run {run_name}: {response.json().get('error').get('message')}")

def cancel_run(run_name, authorization_token):
    url = f"https://management.azure.com/subscriptions/{subscription_id}/resourceGroups/{resource_group_name}/providers/Microsoft.Logic/workflows/{workflow_name}/runs/{run_name}/cancel?api-version={api_version}"
    headers = {
        "Authorization": f"Bearer {authorization_token}"
    }
    response = requests.post(url, headers=headers)
    if response.status_code == 200:
        print(f"Successfully cancelled run {run_name}")
    else:
        print(f"Failed to cancel run {run_name}: {response.json().get('error').get('message')}")


def main():
    authorization_token = get_authorization_token()
    if authorization_token:
        runs = get_runs(authorization_token)
        for run in runs:
            delete_run(run, authorization_token)

if __name__ == "__main__":
    main()
