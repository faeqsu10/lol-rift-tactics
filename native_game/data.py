from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable
from typing import Literal

TeamId = Literal["blue", "red"]
TargetType = Literal["enemy", "self", "all-enemies"]
Role = Literal["Vanguard", "Mage", "Marksman", "Assassin"]
EffectKind = Literal["damage", "shield", "stun"]


@dataclass(frozen=True)
class AbilityEffect:
    kind: EffectKind
    amount: int = 0
    turns: int = 0


@dataclass(frozen=True)
class Ability:
    id: str
    name: str
    description: str
    cooldown: int
    target_type: TargetType
    effects: tuple[AbilityEffect, ...]


@dataclass(frozen=True)
class ChampionBlueprint:
    id: str
    name: str
    title: str
    role: Role
    team: TeamId
    max_hp: int
    speed: int
    accent: str
    abilities: tuple[Ability, ...]


BLUE_TEAM: tuple[ChampionBlueprint, ...] = (
    ChampionBlueprint(
        id="blue-garen",
        name="가렌",
        title="데마시아의 힘",
        role="Vanguard",
        team="blue",
        max_hp=98,
        speed=55,
        accent="#d6b35f",
        abilities=(
            Ability(
                id="decisive-strike",
                name="결정타",
                description="전방으로 돌진해 강한 참격을 가합니다.",
                cooldown=1,
                target_type="enemy",
                effects=(AbilityEffect(kind="damage", amount=18),),
            ),
            Ability(
                id="courage",
                name="용기",
                description="몸을 낮추고 단단한 보호막을 얻습니다.",
                cooldown=2,
                target_type="self",
                effects=(AbilityEffect(kind="shield", amount=22),),
            ),
            Ability(
                id="judgment",
                name="심판",
                description="회전하면서 적 전체를 휩씁니다.",
                cooldown=3,
                target_type="all-enemies",
                effects=(AbilityEffect(kind="damage", amount=12),),
            ),
        ),
    ),
    ChampionBlueprint(
        id="blue-ahri",
        name="아리",
        title="구미호",
        role="Mage",
        team="blue",
        max_hp=78,
        speed=68,
        accent="#ec8d8d",
        abilities=(
            Ability(
                id="orb-of-deception",
                name="현혹의 구슬",
                description="마력을 담은 구슬을 발사합니다.",
                cooldown=1,
                target_type="enemy",
                effects=(AbilityEffect(kind="damage", amount=17),),
            ),
            Ability(
                id="charm",
                name="매혹",
                description="적을 끌어당기며 기절시킵니다.",
                cooldown=3,
                target_type="enemy",
                effects=(
                    AbilityEffect(kind="damage", amount=10),
                    AbilityEffect(kind="stun", turns=1),
                ),
            ),
            Ability(
                id="spirit-rush",
                name="혼령 질주",
                description="빠르게 파고들며 강한 마법 피해를 줍니다.",
                cooldown=3,
                target_type="enemy",
                effects=(AbilityEffect(kind="damage", amount=25),),
            ),
        ),
    ),
    ChampionBlueprint(
        id="blue-jinx",
        name="징크스",
        title="난폭한 말괄량이",
        role="Marksman",
        team="blue",
        max_hp=74,
        speed=72,
        accent="#6dd7d0",
        abilities=(
            Ability(
                id="zap",
                name="빠직!",
                description="장거리 전격 사격으로 적을 꿰뚫습니다.",
                cooldown=1,
                target_type="enemy",
                effects=(AbilityEffect(kind="damage", amount=15),),
            ),
            Ability(
                id="flame-chompers",
                name="와작와작 뻥!",
                description="덫을 던져 적을 폭발과 함께 묶습니다.",
                cooldown=2,
                target_type="enemy",
                effects=(
                    AbilityEffect(kind="damage", amount=8),
                    AbilityEffect(kind="stun", turns=1),
                ),
            ),
            Ability(
                id="super-mega-death-rocket",
                name="초강력 초토화 로켓!",
                description="적 전열 전체를 뒤흔드는 거대 로켓을 발사합니다.",
                cooldown=4,
                target_type="all-enemies",
                effects=(AbilityEffect(kind="damage", amount=14),),
            ),
        ),
    ),
    ChampionBlueprint(
        id="blue-lux",
        name="럭스",
        title="광명의 소녀",
        role="Mage",
        team="blue",
        max_hp=76,
        speed=64,
        accent="#d9c46a",
        abilities=(
            Ability(
                id="light-binding",
                name="빛의 속박",
                description="빛의 구속으로 적을 묶고 피해를 줍니다.",
                cooldown=2,
                target_type="enemy",
                effects=(
                    AbilityEffect(kind="damage", amount=12),
                    AbilityEffect(kind="stun", turns=1),
                ),
            ),
            Ability(
                id="prismatic-barrier",
                name="프리즘 보호막",
                description="빛의 장막으로 자신을 보호합니다.",
                cooldown=2,
                target_type="self",
                effects=(AbilityEffect(kind="shield", amount=20),),
            ),
            Ability(
                id="final-spark",
                name="최후의 섬광",
                description="전장을 가르는 광선으로 적 전체를 타격합니다.",
                cooldown=4,
                target_type="all-enemies",
                effects=(AbilityEffect(kind="damage", amount=13),),
            ),
        ),
    ),
    ChampionBlueprint(
        id="blue-vi",
        name="바이",
        title="필트오버의 집행자",
        role="Vanguard",
        team="blue",
        max_hp=94,
        speed=60,
        accent="#d781b5",
        abilities=(
            Ability(
                id="vault-breaker",
                name="금고 부수기",
                description="강하게 돌진해 적 하나를 강타합니다.",
                cooldown=1,
                target_type="enemy",
                effects=(AbilityEffect(kind="damage", amount=19),),
            ),
            Ability(
                id="blast-shield",
                name="폭발 보호막",
                description="가드 자세를 취해 보호막을 얻습니다.",
                cooldown=2,
                target_type="self",
                effects=(AbilityEffect(kind="shield", amount=18),),
            ),
            Ability(
                id="cease-and-desist",
                name="정지 명령",
                description="적을 추적해 공중으로 띄우듯 제압합니다.",
                cooldown=3,
                target_type="enemy",
                effects=(
                    AbilityEffect(kind="damage", amount=22),
                    AbilityEffect(kind="stun", turns=1),
                ),
            ),
        ),
    ),
    ChampionBlueprint(
        id="blue-ezreal",
        name="이즈리얼",
        title="무모한 탐험가",
        role="Marksman",
        team="blue",
        max_hp=72,
        speed=71,
        accent="#d8b46b",
        abilities=(
            Ability(
                id="mystic-shot",
                name="신비한 화살",
                description="정교한 마력 탄환으로 적 하나를 꿰뚫습니다.",
                cooldown=1,
                target_type="enemy",
                effects=(AbilityEffect(kind="damage", amount=16),),
            ),
            Ability(
                id="arcane-shift",
                name="비전 이동",
                description="짧게 몸을 빼며 마력 보호막을 둘러칩니다.",
                cooldown=2,
                target_type="self",
                effects=(AbilityEffect(kind="shield", amount=16),),
            ),
            Ability(
                id="trueshot-barrage",
                name="정조준 일격",
                description="전장을 가르는 에너지 파동으로 적 전체를 공격합니다.",
                cooldown=4,
                target_type="all-enemies",
                effects=(AbilityEffect(kind="damage", amount=14),),
            ),
        ),
    ),
    ChampionBlueprint(
        id="blue-leona",
        name="레오나",
        title="여명의 방패",
        role="Vanguard",
        team="blue",
        max_hp=100,
        speed=57,
        accent="#d9a957",
        abilities=(
            Ability(
                id="shield-of-daybreak",
                name="여명의 방패",
                description="방패를 내질러 적을 기절시키고 제압합니다.",
                cooldown=2,
                target_type="enemy",
                effects=(
                    AbilityEffect(kind="damage", amount=12),
                    AbilityEffect(kind="stun", turns=1),
                ),
            ),
            Ability(
                id="eclipse",
                name="일식",
                description="황금빛 갑주를 두르고 두터운 보호막을 얻습니다.",
                cooldown=2,
                target_type="self",
                effects=(AbilityEffect(kind="shield", amount=24),),
            ),
            Ability(
                id="solar-flare",
                name="태양 폭발",
                description="태양의 불꽃을 떨어뜨려 적 전체를 태웁니다.",
                cooldown=4,
                target_type="all-enemies",
                effects=(AbilityEffect(kind="damage", amount=11),),
            ),
        ),
    ),
)


RED_TEAM: tuple[ChampionBlueprint, ...] = (
    ChampionBlueprint(
        id="red-darius",
        name="다리우스",
        title="녹서스의 실력자",
        role="Vanguard",
        team="red",
        max_hp=102,
        speed=52,
        accent="#d97d59",
        abilities=(
            Ability(
                id="crippling-strike",
                name="마비의 일격",
                description="도끼를 크게 휘둘러 내려칩니다.",
                cooldown=1,
                target_type="enemy",
                effects=(AbilityEffect(kind="damage", amount=18),),
            ),
            Ability(
                id="defy",
                name="응수",
                description="몸을 굳혀 보호막을 형성합니다.",
                cooldown=2,
                target_type="self",
                effects=(AbilityEffect(kind="shield", amount=20),),
            ),
            Ability(
                id="noxian-guillotine",
                name="녹서스의 단두대",
                description="약한 적을 마무리하는 처형 일격입니다.",
                cooldown=3,
                target_type="enemy",
                effects=(AbilityEffect(kind="damage", amount=28),),
            ),
        ),
    ),
    ChampionBlueprint(
        id="red-annie",
        name="애니",
        title="어둠의 아이",
        role="Mage",
        team="red",
        max_hp=76,
        speed=66,
        accent="#f0b35f",
        abilities=(
            Ability(
                id="disintegrate",
                name="붕괴",
                description="작은 불꽃을 압축해 발사합니다.",
                cooldown=1,
                target_type="enemy",
                effects=(AbilityEffect(kind="damage", amount=16),),
            ),
            Ability(
                id="molten-shield",
                name="용암 방패",
                description="몸을 감싸는 화염 보호막을 만듭니다.",
                cooldown=2,
                target_type="self",
                effects=(AbilityEffect(kind="shield", amount=18),),
            ),
            Ability(
                id="summon-tibbers",
                name="티버 소환",
                description="거대한 폭발로 적 전체를 불태웁니다.",
                cooldown=4,
                target_type="all-enemies",
                effects=(AbilityEffect(kind="damage", amount=13),),
            ),
        ),
    ),
    ChampionBlueprint(
        id="red-caitlyn",
        name="케이틀린",
        title="필트오버의 보안관",
        role="Marksman",
        team="red",
        max_hp=72,
        speed=70,
        accent="#9ab3e6",
        abilities=(
            Ability(
                id="piltover-peacemaker",
                name="필트오버 피스메이커",
                description="정밀한 라이플 사격을 가합니다.",
                cooldown=1,
                target_type="enemy",
                effects=(AbilityEffect(kind="damage", amount=18),),
            ),
            Ability(
                id="yordle-snap-trap",
                name="요들잡이 덫",
                description="적을 묶어 둔 뒤 폭발시킵니다.",
                cooldown=2,
                target_type="enemy",
                effects=(
                    AbilityEffect(kind="damage", amount=9),
                    AbilityEffect(kind="stun", turns=1),
                ),
            ),
            Ability(
                id="ace-in-the-hole",
                name="비장의 한 발",
                description="집중 사격으로 적 하나를 꿰뚫습니다.",
                cooldown=3,
                target_type="enemy",
                effects=(AbilityEffect(kind="damage", amount=25),),
            ),
        ),
    ),
    ChampionBlueprint(
        id="red-morgana",
        name="모르가나",
        title="타락한 자",
        role="Mage",
        team="red",
        max_hp=80,
        speed=62,
        accent="#7d64bf",
        abilities=(
            Ability(
                id="dark-binding",
                name="어둠의 속박",
                description="검은 사슬로 적을 묶고 피해를 입힙니다.",
                cooldown=2,
                target_type="enemy",
                effects=(
                    AbilityEffect(kind="damage", amount=11),
                    AbilityEffect(kind="stun", turns=1),
                ),
            ),
            Ability(
                id="black-shield",
                name="칠흑의 방패",
                description="어둠의 장막으로 자신을 지켜냅니다.",
                cooldown=2,
                target_type="self",
                effects=(AbilityEffect(kind="shield", amount=22),),
            ),
            Ability(
                id="soul-shackles",
                name="영혼의 족쇄",
                description="영혼 사슬로 적 전체를 뒤흔듭니다.",
                cooldown=4,
                target_type="all-enemies",
                effects=(AbilityEffect(kind="damage", amount=12),),
            ),
        ),
    ),
    ChampionBlueprint(
        id="red-yasuo",
        name="야스오",
        title="용서받지 못한 자",
        role="Marksman",
        team="red",
        max_hp=82,
        speed=74,
        accent="#7aa4cd",
        abilities=(
            Ability(
                id="steel-tempest",
                name="강철 폭풍",
                description="날카로운 찌르기로 적 하나를 베어냅니다.",
                cooldown=1,
                target_type="enemy",
                effects=(AbilityEffect(kind="damage", amount=17),),
            ),
            Ability(
                id="wind-wall",
                name="바람 장막",
                description="순간적인 바람 결계로 자신을 보호합니다.",
                cooldown=2,
                target_type="self",
                effects=(AbilityEffect(kind="shield", amount=16),),
            ),
            Ability(
                id="last-breath",
                name="최후의 숨결",
                description="거센 돌진 후 강력한 일격을 꽂아 넣습니다.",
                cooldown=3,
                target_type="enemy",
                effects=(AbilityEffect(kind="damage", amount=23),),
            ),
        ),
    ),
    ChampionBlueprint(
        id="red-zed",
        name="제드",
        title="그림자의 주인",
        role="Assassin",
        team="red",
        max_hp=78,
        speed=73,
        accent="#8e6a6a",
        abilities=(
            Ability(
                id="razor-shuriken",
                name="예리한 표창",
                description="그림자 표창으로 적 하나를 정확히 찌릅니다.",
                cooldown=1,
                target_type="enemy",
                effects=(AbilityEffect(kind="damage", amount=17),),
            ),
            Ability(
                id="living-shadow",
                name="살아있는 그림자",
                description="그림자 속으로 숨어 순간적인 보호를 얻습니다.",
                cooldown=2,
                target_type="self",
                effects=(AbilityEffect(kind="shield", amount=16),),
            ),
            Ability(
                id="death-mark",
                name="죽음의 표식",
                description="표식을 새긴 뒤 폭발적인 일격으로 마무리합니다.",
                cooldown=3,
                target_type="enemy",
                effects=(AbilityEffect(kind="damage", amount=24),),
            ),
        ),
    ),
    ChampionBlueprint(
        id="red-lissandra",
        name="리산드라",
        title="얼음 마녀",
        role="Mage",
        team="red",
        max_hp=82,
        speed=61,
        accent="#6fb1d4",
        abilities=(
            Ability(
                id="ice-shard",
                name="얼음 파편",
                description="차가운 파편을 발사해 적을 꿰뚫습니다.",
                cooldown=1,
                target_type="enemy",
                effects=(AbilityEffect(kind="damage", amount=15),),
            ),
            Ability(
                id="ring-of-frost",
                name="서릿발",
                description="냉기를 폭발시켜 적을 얼려 묶습니다.",
                cooldown=2,
                target_type="enemy",
                effects=(
                    AbilityEffect(kind="damage", amount=9),
                    AbilityEffect(kind="stun", turns=1),
                ),
            ),
            Ability(
                id="frozen-tomb",
                name="얼음 무덤",
                description="냉기의 폭발로 적 전체를 뒤덮습니다.",
                cooldown=4,
                target_type="all-enemies",
                effects=(AbilityEffect(kind="damage", amount=12),),
            ),
        ),
    ),
)


ALL_BLUEPRINTS: tuple[ChampionBlueprint, ...] = (*BLUE_TEAM, *RED_TEAM)
BLUEPRINTS_BY_ID: dict[str, ChampionBlueprint] = {blueprint.id: blueprint for blueprint in ALL_BLUEPRINTS}
DEFAULT_BLUE_IDS: tuple[str, str, str] = ("blue-garen", "blue-ahri", "blue-jinx")
DEFAULT_RED_IDS: tuple[str, str, str] = ("red-darius", "red-annie", "red-caitlyn")
SELECTABLE_BLUE_IDS: tuple[str, ...] = tuple(blueprint.id for blueprint in BLUE_TEAM)
SELECTABLE_RED_IDS: tuple[str, ...] = tuple(blueprint.id for blueprint in RED_TEAM)


def build_battle_blueprints(
    blue_ids: Iterable[str] | None = None,
    red_ids: Iterable[str] | None = None,
) -> tuple[ChampionBlueprint, ...]:
    selected_blue_ids = tuple(blue_ids or DEFAULT_BLUE_IDS)
    selected_red_ids = tuple(red_ids or DEFAULT_RED_IDS)

    blue_lineup = tuple(
        BLUEPRINTS_BY_ID[blueprint_id]
        for blueprint_id in selected_blue_ids
        if blueprint_id in BLUEPRINTS_BY_ID and BLUEPRINTS_BY_ID[blueprint_id].team == "blue"
    )
    red_lineup = tuple(
        BLUEPRINTS_BY_ID[blueprint_id]
        for blueprint_id in selected_red_ids
        if blueprint_id in BLUEPRINTS_BY_ID and BLUEPRINTS_BY_ID[blueprint_id].team == "red"
    )

    return (*blue_lineup, *red_lineup)
