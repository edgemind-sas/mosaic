import mosaic.trading as mtr
import yaml

with open("bot.yaml", 'r', encoding="utf-8") as yaml_file:
    bot_config = yaml.load(yaml_file,
                           Loader=yaml.SafeLoader)
    bot_config["bot"].setdefault("cls", "BotTrading")
    bot = mtr.BotTrading.from_dict(bot_config["bot"])

bot.start(
    data_dir=".",
    progress_mode=True,
)

print(bot.portfolio)
