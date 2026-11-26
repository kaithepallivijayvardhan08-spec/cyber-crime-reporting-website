"""Create an admin/investigator account in the configured CyberSafe database.

Use this only for local setup or recovery. For normal staff onboarding, sign in
to the separate admin console and create the account there.

Run from the backend folder with its virtual environment active:
    py create_staff_account.py
"""
from getpass import getpass
from pathlib import Path
import sys

from dotenv import load_dotenv

# Load the backend .env even if this script is launched from another folder.
load_dotenv(Path(__file__).resolve().parent / ".env")

from models.user import User
from utils.validators import (
    validate_email,
    validate_indian_mobile,
    validate_password,
)


def ask_required(label):
    value = input(label).strip()
    if not value:
        raise ValueError("This field is required.")
    return value


def main():
    print("CyberSafe staff account setup")
    print("Creates an admin/investigator in the existing CyberSafe database.")
    print("")

    full_name = ask_required("Full name: ")
    if len(full_name) > 100:
        raise ValueError("Name must be 100 characters or fewer.")

    email = ask_required("Email: ").lower()
    if len(email) > 100 or not validate_email(email):
        raise ValueError("Enter a valid email address (up to 100 characters).")

    phone = ask_required("10-digit Indian mobile number: ")
    if not validate_indian_mobile(phone):
        raise ValueError(
            "Phone must have 10 digits, start with 6-9, and not repeat one digit."
        )

    role = input("Role (admin/investigator): ").strip().lower()
    if role not in {"admin", "investigator"}:
        raise ValueError("Choose either admin or investigator.")

    password = getpass("Password (hidden): ")
    valid, message = validate_password(password)
    if not valid:
        raise ValueError(message)

    confirmation = getpass("Confirm password: ")
    if password != confirmation:
        raise ValueError("Passwords do not match.")

    confirm = input(
        f"Create {role} account for {email}? Type YES to continue: "
    ).strip()
    if confirm != "YES":
        print("Cancelled. No account was created.")
        return

    # User.create_staff_user uses the same validators and password hashing
    # as the application's account model. Database unique indexes handle races.
    account_id = User.create_staff_user(
        full_name=full_name,
        email=email,
        phone=phone,
        password=password,
        role=role,
    )

    print("")
    print(f"Created {role} account successfully. User ID: {account_id}")
    print("You can now sign in to the CyberSafe website or admin console.")


if __name__ == "__main__":
    try:
        main()
    except ValueError as error:
        print(f"\nNo account created: {error}")
        sys.exit(1)
    except KeyboardInterrupt:
        print("\nCancelled. No account was created.")
        sys.exit(1)
    except Exception as error:
        # Do not print SQL details, environment values, or password input.
        print(f"\nAccount creation failed ({type(error).__name__}).")
        print("Check the backend .env and database connection, then retry.")
        sys.exit(1)
