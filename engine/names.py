import random

FIRST_NAMES = [
    "Aaron", "Andre", "Anthony", "Blake", "Brandon", "Brian", "Cameron", "Carlos",
    "Chad", "Chris", "Clarence", "Corey", "Curtis", "Damon", "Daniel", "Darrell",
    "David", "Deion", "Derek", "Deshawn", "Devon", "Dominic", "Donovan", "Douglas",
    "Dwayne", "Eric", "Ethan", "Evan", "Frank", "Frederick", "Garrett", "Gary",
    "George", "Hector", "Isaiah", "Jackson", "Jamal", "James", "Jared", "Jason",
    "Jerome", "Jesse", "Jordan", "Joseph", "Joshua", "Justin", "Keith", "Kevin",
    "Kyle", "Lamar", "Lance", "Larry", "Leon", "Leonard", "Lorenzo", "Marcus",
    "Mark", "Martin", "Matthew", "Maurice", "Michael", "Miles", "Nathan", "Nicholas",
    "Patrick", "Paul", "Raymond", "Reggie", "Ricardo", "Richard", "Robert", "Ronald",
    "Russell", "Ryan", "Samuel", "Scott", "Sean", "Stephen", "Steven", "Terrell",
    "Thomas", "Timothy", "Travis", "Trevor", "Troy", "Tyler", "Victor", "Vincent",
    "Walter", "Wesley", "William", "Xavier", "Zach", "Malik", "Darius", "Kendrick",
]

LAST_NAMES = [
    "Adams", "Alexander", "Allen", "Anderson", "Bailey", "Baker", "Barnes", "Bell",
    "Bennett", "Brooks", "Brown", "Bryant", "Butler", "Campbell", "Carter", "Clark",
    "Coleman", "Collins", "Cook", "Cooper", "Cox", "Crawford", "Davis", "Dixon",
    "Edwards", "Evans", "Ferguson", "Fisher", "Ford", "Foster", "Franklin", "Freeman",
    "Gibson", "Gordon", "Graham", "Grant", "Gray", "Green", "Griffin", "Hall",
    "Hamilton", "Harris", "Harrison", "Hayes", "Henderson", "Hill", "Howard", "Hudson",
    "Hughes", "Hunter", "Jackson", "Jenkins", "Johnson", "Jones", "Jordan", "Kelly",
    "King", "Lewis", "Long", "Martin", "Mason", "Matthews", "Mitchell", "Moore",
    "Morgan", "Morris", "Murphy", "Murray", "Nelson", "Parker", "Patterson", "Perry",
    "Peterson", "Phillips", "Price", "Reed", "Reynolds", "Richardson", "Rivera",
    "Roberts", "Robinson", "Rogers", "Ross", "Russell", "Sanders", "Scott", "Shaw",
    "Simpson", "Smith", "Stewart", "Sullivan", "Taylor", "Thomas", "Thompson", "Turner",
    "Walker", "Ward", "Washington", "Watson", "White", "Williams", "Wilson", "Wood",
]

CITIES = [
    "Ironforge", "Stormhaven", "Crystalbrook", "Shadowmere",
    "Ashfield", "Dunmoor", "Silverpeak", "Thornwall",
    "Gloomhaven", "Embervale", "Frostgate", "Duskwood",
    "Grimrock", "Blazeholm", "Stonecliff", "Coldwater",
    "Darkridge", "Ravenspire", "Copperhold", "Mistwood",
    "Ironcrest", "Wolfhaven", "Dragonsreach", "Steelport",
    "Nightfall", "Dawnshire", "Cinderfield", "Saltmarsh",
    "Oakenveil", "Thornfield", "Galeford", "Highwatch",
]

TEAM_NAMES = [
    "Thunderhawks", "Iron Bears", "Storm Ravens", "Crimson Wolves",
    "Steel Titans", "Frost Giants", "Shadow Foxes", "Ember Lions",
    "Stone Eagles", "Dark Knights", "Blaze Stallions", "Cold Sharks",
    "Grim Sentinels", "Crystal Falcons", "Night Owls", "Dawn Riders",
    "Cinder Vipers", "Salt Marlins", "Oak Stags", "Thorn Rams",
    "Gale Hawks", "High Phoenix", "Thunder Jaguars", "Steel Serpents",
    "Shadow Lynx", "Ember Wolves", "Iron Grizzlies", "Storm Riders",
    "Frost Ravens", "Dark Stallions", "Silver Titans", "Blaze Panthers",
]

ABBREVIATIONS = [
    "IFT", "SHB", "CRV", "SMW", "AFT", "DMG", "SPF", "TWL",
    "GHE", "EVK", "FGG", "DWS", "GRS", "BHC", "SCO", "CWR",
    "DRN", "RSP", "CHG", "MWM", "ICS", "WHX", "DRT", "STS",
    "NFS", "DSR", "CFC", "SMM", "OVR", "TFD", "GFF", "HWP",
]

CONFERENCES = ["AFC", "NFC"]
DIVISIONS = ["North", "South", "East", "West"]


def random_player_name():
    return f"{random.choice(FIRST_NAMES)} {random.choice(LAST_NAMES)}"


def get_team_configs(num_teams=32):
    teams = []
    idx = 0
    for conf in CONFERENCES:
        for div in DIVISIONS:
            for _ in range(num_teams // 8):
                teams.append({
                    "city": CITIES[idx % len(CITIES)],
                    "name": TEAM_NAMES[idx % len(TEAM_NAMES)],
                    "abbreviation": ABBREVIATIONS[idx % len(ABBREVIATIONS)],
                    "conference": conf,
                    "division": div,
                })
                idx += 1
    return teams
