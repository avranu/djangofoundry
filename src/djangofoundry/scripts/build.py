import argparse
import logging
import subprocess

import toml

logging.basicConfig(level=logging.INFO)

class PackageUploader:
    def __init__(self, toml_file):
        self.toml_file = toml_file
        self.config = self.load_config()

    def load_config(self):
        try:
            with open(self.toml_file, "r") as file:
                return toml.load(file)
        except FileNotFoundError as e:
            logging.error(f"Error loading TOML file: {e}")
            raise

    def save_config(self):
        try:
            with open(self.toml_file, "w") as file:
                toml.dump(self.config, file)
        except IOError as e:
            logging.error(f"Error saving TOML file: {e}")
            raise

    def update_minor_version(self):
        version = self.config["tool"]["poetry"]["version"]
        major, minor, patch = map(int, version.split("."))
        minor += 1
        self.config["tool"]["poetry"]["version"] = f"{major}.{minor}.{patch}"
        logging.info(f"Updated version to {major}.{minor}.{patch}")

    def build_package(self):
        try:
            subprocess.run(["python", "-m", "build"], check=True)
            logging.info("Package built successfully")
        except subprocess.CalledProcessError as e:
            logging.error(f"Error during build: {e}")
            raise

    def upload_package(self):
        package_name = self.config["tool"]["poetry"]["name"]
        version = self.config["tool"]["poetry"]["version"]
        major, minor, _ = map(int, version.split("."))
        upload_pattern = f"dist/{package_name}-{major}.{minor}*"

        try:
            subprocess.run(["python", "-m", "twine", "upload", upload_pattern], check=True)
            logging.info("Package uploaded successfully")
        except subprocess.CalledProcessError as e:
            logging.error(f"Error during upload: {e}")
            raise


    def update_and_upload(self):
        self.update_minor_version()
        self.save_config()
        self.build_package()
        self.upload_package()

def main(args):
    uploader = PackageUploader(args.toml_file)
    uploader.update_and_upload()

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Update and upload a Python package")
    parser.add_argument("-t", "--toml-file", default="pyproject.toml", help="Path to the pyproject.toml file")
    args = parser.parse_args()

    main(args)
