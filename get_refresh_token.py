import requests
import sys

def main():
    print("=== Google Ads Refresh Token Generator ===\n")
    client_id = input("1. Paste your Google Cloud Client ID: ").strip()
    client_secret = input("2. Paste your Google Cloud Client Secret: ").strip()
    
    redirect_uri = "http://127.0.0.1"
    
    auth_url = (
        f"https://accounts.google.com/o/oauth2/v2/auth?"
        f"client_id={client_id}&"
        f"redirect_uri={redirect_uri}&"
        f"response_type=code&"
        f"scope=https://www.googleapis.com/auth/adwords&"
        f"access_type=offline&"
        f"prompt=consent"
    )
    
    print("\n------------------------------------------------------------")
    print("3. Click this link and sign in with your Google Ads account:")
    print(auth_url)
    print("------------------------------------------------------------\n")
    print("After you click 'Allow', you will be redirected to a URL that starts with http://127.0.0.1/?code=...")
    print("Copy the ENTIRE URL you were redirected to and paste it here.")
    
    redirect_url = input("\n4. Paste the full redirect URL here: ").strip()
    
    try:
        # Extract the code from the URL
        code_part = redirect_url.split("code=")[1].split("&")[0]
        # Some URLs have %2F which needs to be decoded
        import urllib.parse
        auth_code = urllib.parse.unquote(code_part)
    except IndexError:
        print("\nERROR: Could not find 'code=' in the URL you pasted.")
        return
        
    print("\nFetching your Refresh Token...")
    payload = {
        "client_id": client_id,
        "client_secret": client_secret,
        "code": auth_code,
        "grant_type": "authorization_code",
        "redirect_uri": redirect_uri
    }
    
    try:
        resp = requests.post("https://oauth2.googleapis.com/token", data=payload)
        resp.raise_for_status()
        data = resp.json()
        print("\n✅ SUCCESS!")
        print(f"\nYour Refresh Token is:\n{data.get('refresh_token')}\n")
        print("Copy this token and add it to the .env file in your tiqets-ads-sync repository!")
    except Exception as e:
        print("\n❌ Error generating token.")
        print(e)
        if hasattr(e, 'response') and e.response is not None:
            print(e.response.text)

if __name__ == "__main__":
    main()
