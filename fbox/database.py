import shutil, asyncio

from fbox import settings
from fbox.log import logger
from fbox.utils import get_now
from fbox.files.models import Box, File, IPUser
from fbox.files.choices import StatusChoice
from fbox.files.storage import storage
from fbox.cards.models import Card


class BoxDatabaseMixin:
    boxes: dict[str, Box] = {}
    expired_boxes: list[Box] = []

    async def init_boxes(self) -> None:
        logger.info(f"Initialize boxes")
        box_codes = await storage.get_dir_filenames("box")

        for box_code in box_codes:
            box = await storage.get_box(box_code)
            if box is None:
                await storage.remove_box(box_code)
                continue

            if self.check_box_expire(box):
                logger.debug(f"Box {box.code} expire")
                self.expire_box(box)
                continue

            logger.debug(f"Box {box.code} valid")
            self.boxes[box.code] = box

        logger.info(f"Initialize boxes finishied")

    async def clean_expired_boxes(self) -> None:
        logger.info(f"Check {len(self.boxes)} box")
        box_codes = list(self.boxes.keys())
        for code in box_codes:
            box = self.boxes[code]
            if self.check_box_expire(box):
                self.expire_box(box)

        logger.info(f"Box count {len(self.boxes)}, expired {len(self.expired_boxes)}")
        for box in self.expired_boxes:
            await storage.archive_box(box)

        self.expired_boxes.clear()
        logger.info(f"Clean box finished")

    def check_box_expire(self, box: Box) -> bool:
        now = int(get_now().timestamp())
        passed = now - box.created

        logger.debug(f"Box {box.code} with status {box.status} passed {passed} seconds")

        waiting_expire = box.status == StatusChoice.waiting and passed >= (
            settings.BOX_EXPIRE / 10
        )
        complete_expire = (
            box.status == StatusChoice.complete and passed >= settings.BOX_EXPIRE
        )

        if waiting_expire or complete_expire:
            return True
        return False

    def check_box_by_code(self, code: str) -> bool:
        return code in self.boxes or code in self.expired_boxes

    def get_box(self, code: str) -> Box | None:
        box = self.boxes.get(code)
        if box and self.check_box_expire(box):
            self.expire_box(box)
            return None
        return box

    def get_boxes(self, expired: bool) -> list[Box]:
        if expired:
            return self.expired_boxes
        return list(self.boxes.values())

    async def save_box(self, box: Box) -> None:
        self.boxes[box.code] = box
        await storage.save_box(box)

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

    async def init_cards(self) -> None:
        logger.info(f"Initialize cards")

        card_json_names = await storage.get_dir_filenames("card")

        for card_json_name in card_json_names:
            card_code = card_json_name.split(".")[0]
            card = await storage.get_card(card_code)
            if card is None:
                continue

            if self.check_card_expire(card):
                logger.debug(f"Card {card.code} expire")
                self.expire_card(card)
                continue

            logger.debug(f"Card {card.code} valid")
            self.cards[card.code] = card

        logger.info(f"Initialize cards finishied")

    def check_card_expire(self, card: Card) -> bool:
        now = int(get_now().timestamp())

        logger.debug(
            f"Card {card.code} count {card.count} passed {now - card.created} seconds"
        )

        if card.created > 0 and (now - card.created) >= (365 * 24 * 3600):
            return True

        if card.count == 0:
            return True

        return False

    def check_card_by_code(self, code: str) -> bool:
        return code in self.cards or code in self.expired_cards

    def get_card(self, code: str) -> Card | None:
        card = self.cards.get(code)
        if card and self.check_card_expire(card):
            self.expire_card(card)
            return None
        return card

    async def save_card(self, card: Card) -> None:
        self.cards[card.code] = card
        await storage.save_card(card)

    def expire_card(self, card: Card) -> None:
        self.expired_cards.append(card.code)

        if self.check_card_by_code(card.code):
            del self.cards[card.code]


class IPUserDatabaseMixin:
    ip_users: dict[str, IPUser] = {}

    def clean_expire_ip_user(self) -> None:
        now = int(get_now().timestamp())
        logger.info(f"IP users count {len(self.ip_users)}")
        logger.info(f"Clean ip users")
        expired = []

        for ip_user in self.ip_users.values():
            error_expire = (now - ip_user.error_from) > 3600
            box_expire = (now - ip_user.box_from) > 3600
            file_expire = (now - ip_user.file_from) > 3600

            logger.debug(
                f"{ip_user.ip} error {error_expire}, box {box_expire}, file {file_expire}"
            )

            if error_expire and box_expire and file_expire:
                expired.append(ip_user.ip)
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

        for ip in expired:
            del self.ip_users[ip]

        logger.info(f"Clean {len(expired)} ip users finishied")

    def get_ip_user(self, ip: str) -> IPUser | None:
        return self.ip_users.get(ip)

    def save_ip_user(self, ip_user: IPUser) -> None:
        self.ip_users[ip_user.ip] = ip_user


class Database(BoxDatabaseMixin, CardDatabaseMixin, IPUserDatabaseMixin):
    async def init_db(self) -> None:
        await storage.init_root()

        await self.init_boxes()
        await self.init_cards()


db = Database()
