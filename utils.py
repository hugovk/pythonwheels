import datetime
import json
import pytz
import requests
from packaging.metadata import Metadata


BASE_URL = "https://pypi.org/pypi"

DEPRECATED_PACKAGES = {
    "BeautifulSoup",
    "bs4",
    "distribute",
    "django-social-auth",
    "nose",
    "pep8",
    "pycrypto",
    "pypular",
    "sklearn",
}

SESSION = requests.Session()


def get_json_url(package_name):
    return BASE_URL + "/" + package_name + "/json"


def annotate_wheels(packages):
    print("Getting dependency data...")
    num_packages = len(packages)
    for index, package in enumerate(packages):
        print(index + 1, num_packages, package["name"])
        depends_on_six = False
        url = get_json_url(package["name"])
        response = SESSION.get(url)
        if response.status_code != 200:
            print(" ! Skipping " + package["name"])
            continue
        data = response.json()
        requires_dist = data["info"]["requires_dist"]
        if requires_dist:
            meta = Metadata.from_raw({"requires_dist": requires_dist}, validate=False)
            if any(requirement.name == "six" for requirement in meta.requires_dist):
                depends_on_six = True

        package["wheel"] = depends_on_six

        # Display logic. I know, I'm sorry.
        package["value"] = 1
        if depends_on_six:
            package["css_class"] = "default"
            package["icon"] = "\u2717"  # Ballot X
            package["title"] = "This package depends on six."
        else:
            package["css_class"] = "success"
            package["icon"] = "\u2713"  # Check mark
            package["title"] = "This package does not depend on six."


def get_top_packages():
    print("Getting packages...")

    with open("top-pypi-packages.json") as data_file:
        packages = json.load(data_file)["rows"]

    # Rename keys
    for package in packages:
        package["downloads"] = package.pop("download_count")
        package["name"] = package.pop("project")

    return packages


def not_deprecated(package):
    return package["name"] not in DEPRECATED_PACKAGES


def remove_irrelevant_packages(packages, limit):
    print("Removing cruft...")
    active_packages = list(filter(not_deprecated, packages))
    return active_packages[:limit]


def save_to_file(packages, file_name):
    now = datetime.datetime.utcnow().replace(tzinfo=pytz.utc)
    with open(file_name, "w") as f:
        f.write(
            json.dumps(
                {
                    "data": packages,
                    "last_update": now.strftime("%A, %d %B %Y, %X %Z"),
                },
                indent=1,
            )
        )
