import shutil, asyncio

from fbox import settings
from fbox.utils import get_now
from fbox.files.models import Box, File, IPUser
from fbox.files.choices import StatusChoice
from fbox.cards.models import Card


class BoxDatabaseMixin:
    boxes: dict[str, Box] = {}
    expired_boxes: list[Box] = []

    def init_boxes(self) -> None:
        box_data = settings.DATA_ROOT / "box"
        for box_path in box_data.iterdir():
            box_code = box_path.name
            box_dir = box_data / box_code
            box_json = box_dir / "box.json"

            if not box_json.exists():
                shutil.rmtree(box_dir)
                continue

            box = Box.parse_file(box_json)

            if self.check_box_expire(box):
                self.expire_box(box)
                continue

            self.boxes[box.code] = box

    def archive_box(self, box: Box) -> None:
        now = get_now()
        current = settings.DATA_ROOT / "box" / box.code
        target = settings.LOGS_ROOT / "box" / box.code / now.isoformat()
        target.mkdir(parents=True)

        for f in current.iterdir():
            shutil.move(f, target)
        current.rmdir()

    async def clean_expired_boxes(self) -> None:
        for box in self.expired_boxes:
            await asyncio.to_thread(self.archive_box, box)

    def check_box_expire(self, box: Box) -> bool:
        now = int(get_now().timestamp())
        passed = now - box.created

        waiting_expire = box.status == StatusChoice.waiting and passed >= (2 * 3600)
        complete_expire = box.status == StatusChoice.complete and passed >= (24 * 3600)

        if waiting_expire or complete_expire:
            return True
        return False

    def check_box_by_code(self, code: str) -> bool:
        return code in self.boxes

    def get_box(self, code: str) -> Box | None:
        box = self.boxes.get(code)
        if self.check_box_expire(box):
            self.expire_box(box)
            return None
        return box

    def save_box_file(self, box: Box) -> None:
        box_file = settings.DATA_ROOT / "box" / box.code / "box.json"
        with open(box_file, "w") as f:
            f.write(box.json())

    async def save_box(self, box: Box) -> None:
        self.boxes[box.code] = box
        await asyncio.to_thread(self.save_box_file, box)

    def expire_box(self, box: Box) -> None:
        self.expired_boxes.append(box)

        if self.check_box_by_code(box.code):
            del self.boxes[box.code]

    def get_file(self, code: str, filename: str) -> File | None:
        box = self.boxes.get(code)
        if box:
            if self.check_box_expire(box):
                self.expire_box(box)
                return None

            file = box.files.get(filename)
            if file:
                return file
        return None

    def get_files(self, code: str) -> list[File] | None:
        box = self.boxes.get(code)
        if box:
            if self.check_box_expire(box):
                self.expire_box(box)
                return None

            return list(box.files.values())
        return None


class CardDatabaseMixin:
    cards: dict[str, Card] = {}
    expired_cards: list[str] = []

    def init_cards(self) -> None:
        card_data = settings.DATA_ROOT / "card"
        for card_path in card_data.iterdir():
            card_json = card_data / card_path.name
            card = Card.parse_file(card_json)

            if self.check_card_expire(card):
                self.expire_card(card)
                continue

            self.cards[card.code] = card

    def check_card_expire(self, card: Card) -> bool:
        now = int(get_now().timestamp())

        if card.created > 0 and (now - card.created) >= (365 * 24 * 3600):
            return True

        if card.count == 0:
            return True

        return False

    def check_card_by_code(self, code: str) -> bool:
        return code in self.cards or code in self.expired_cards

    def get_card(self, code: str) -> Card | None:
        card = self.cards.get(code)
        if self.check_card_expire(card):
            self.expire_card(card)
            return None
        return card

    def save_card_file(self, card: Card) -> None:
        card_file = settings.DATA_ROOT / "card" / f"{card.code}.json"
        with open(card_file, "w") as f:
            f.write(card.json())

    async def save_card(self, card: Card) -> None:
        self.cards[card.code] = card
        await asyncio.to_thread(self.save_card_file, card)

    def expire_card(self, card: Card) -> None:
        self.expired_cards.append(card.code)

        if self.check_card_by_code(card.code):
            del self.cards[card.code]


class IPUserDatabaseMixin:
    ip_users: dict[str, IPUser] = {}

    def clean_expire_ip_user(self) -> None:
        now = int(get_now().timestamp())

        for ip_user in self.ip_users.values():
            error_expire = (now - ip_user.error_from) > 3600
            box_expire = (now - ip_user.box_from) > 3600
            file_expire = (now - ip_user.file_from) > 3600

            if error_expire and box_expire and file_expire:
                del self.ip_users[ip_user.ip]
            else:
                if error_expire:
                    ip_user.error_count = 0
                    ip_user.error_from = 0

                if box_expire:
                    ip_user.box_count = 0
                    ip_user.box_from = 0
                
                if file_expire:
                    ip_user.file_count = 0
                    ip_user.file_from = 0

                self.save_ip_user(ip_user)

    def get_ip_user(self, ip: str) -> IPUser | None:
        return self.ip_users.get(ip)

    def save_ip_user(self, ip_user: IPUser) -> None:
        self.ip_users[ip_user.ip] = ip_user


class Database(BoxDatabaseMixin, CardDatabaseMixin, IPUserDatabaseMixin):
    def __init__(self) -> None:
        if not settings.DATA_ROOT.exists():
            settings.DATA_ROOT.mkdir(parents=True)

        box_data = settings.DATA_ROOT / "box"
        if not box_data.exists():
            box_data.mkdir(parents=True)
        else:
            self.init_boxes()

        card_data = settings.DATA_ROOT / "card"
        if not card_data.exists():
            card_data.mkdir(parents=True)
        else:
            self.init_cards()


db = Database()
