from io import BytesIO
import discord
from discord.ui import Button, View
import src.leelazGo
import re
import time

process = None
is_active = False
msg = None
win_rate = '100'
bot_rate = ''
turn = 'W'


async def is_go_action(message, content):
    global bot_rate
    select_key = '([A-Z,a-z])([0-1]?[0-9]?)'
    launch_key = '下棋-?([a-zA-Z0-9]+)'
    if '下棋' in content:
        if re.search(launch_key, content):
            if len(re.search(launch_key, content).groups()) > 0:
                bot_rate = await launch_go(message, re.search(launch_key, content).groups()[0].upper())
                return True
        else:
            bot_rate = await launch_go(message, 'best-network')
            return True
    elif re.search(select_key, content):
        if len(re.search(select_key, content).groups()) > 1:
            x_coord = re.search(select_key, content).groups()[0]
            y_coord = str(int(re.search(select_key, content).groups()[1]))
            await send_move(message, x_coord, y_coord)
            return True
        else:
            await message.channel.send('下棋指令錯誤 格式應該是 : !D12')
            return False
    elif content == '換妳' or content == '換你':
        await bot_respond(message)
        return True
    elif content == '棋局' or content == '進度':
        await show_board(message, False, [], [])
        return True
    elif content == '顯示手數' or content == '顯示手順' or content == '手數' or content == '手順':
        await show_board(message, True, [], [])
        return True
    elif content == '推薦' or content == '好點三選一' or content == '建議':
        await recommand(message)
        return True
    elif content == '分析':
        await score(message)
        return True
    elif content == '點空':
        await estimate_score(message)
        return True
    elif content == '結束' or content == '結算':
        await end_game(message)
        return True
    elif content == '天元':
        await send_move(message, 'K', '10')
        return True
    elif content == '左下星位':
        await send_move(message, 'D', '4')
        return True
    elif content == '左上星位':
        await send_move(message, 'D', '16')
        return True
    elif content == '右下星位':
        await send_move(message, 'Q', '4')
        return True
    elif content == '右上星位':
        await send_move(message, 'Q', '16')
        return True
    elif content == '悔棋':
        await undo_game(message)
        return True
    elif content == '虛手':
        await pass_move(message)
        return True
    elif content == '讀檔':
        await try_load_game(message)
        return True
    elif content == '存檔':
        await try_save_game(message)
        return True
    else:
        return False


async def launch_go(message, level):
    global process, is_active
    if not is_active:
        await message.channel.send('啟動中')
        process = src.leelazGo.run_leelaz(level)
        if process != None:
            await message.channel.send('啟動完成')
            is_active = True
            await show_board(message, False, [], [])
            return level
        else:
            await message.channel.send('啟動失敗，目前不支援: ' + level + ' 喔~，目前有 20K、15K、11K、7K、5K、3K、1K、1D、3D、5D、7D、9D、11D')
            return ' '
    else:
        await message.channel.send('現在有正在進行的棋局喔')
        await show_board(message, False, [], [])
        return bot_rate


async def send_move(message, x_coord, y_coord):
    global turn
    if is_active:
        if bot_rate == '對局':
            turn = 'B' if turn == 'W' else 'W'
        else:
            turn = 'B'

        if not src.leelazGo.add_move(process, turn, x_coord+y_coord):
            turn = 'B' if turn == 'W' else 'W'
            await message.channel.send('這裡不能下')
        else:
            await show_board(message, False, [], [])

            if not bot_rate == '對局':
                time.sleep(1)
                await bot_respond(message)
    else:
        await message.channel.send('目前沒有正在進行的棋局喔')


async def pass_move(message):
    global turn
    if is_active:
        if bot_rate == '對局':
            turn = 'B' if turn == 'W' else 'W'
        else:
            turn = 'B'

        if not src.leelazGo.add_move(process, turn, 'pass'):
            turn = 'B' if turn == 'W' else 'W'
            await message.channel.send('這裡不能下')
        else:
            await show_board(message, False, [], [])

            if not bot_rate == '對局':
                time.sleep(1)
                await bot_respond(message)
    else:
        await message.channel.send('目前沒有正在進行的棋局喔')


async def estimate_score(message):
    global turn
    if is_active:
        await message.channel.send('我算算看喔...')
        sum, result = src.leelazGo.estimate_score(process)
        sum += 6.5
        await show_board(message, False, [], result)
        if sum > 0:
            await message.channel.send('白優 ' + str(abs(sum)) + ' 目')
        elif sum == 0:
            await message.channel.send('平局')
        elif sum < 0:
            await message.channel.send('黑優 ' + str(abs(sum)) + ' 目')

    else:
        await message.channel.send('目前沒有正在進行的棋局喔')


async def recommand(message):
    global msg
    if is_active:
        await message.channel.send('我想想怎麼下喔...')
        recommand_positions = src.leelazGo.think(process, 5)

        if len(recommand_positions) > 5:
            await show_board(message, False, recommand_positions[0:5], [])
        else:
            await show_board(message, False, recommand_positions, [], [])

        await message.channel.send('感覺這些地方都不錯 ~')
    else:
        await message.channel.send('目前沒有正在進行的棋局喔')


async def show_board(message, show_text, recommand_positions, score_estimate):
    global msg
    if is_active:
        with BytesIO() as image_binary:
            src.leelazGo.show_board_GUI(
                process, show_text, recommand_positions, score_estimate).save(image_binary, 'PNG')
            image_binary.seek(0)

            if msg != None:
                await msg.delete()

            msg = await message.channel.send(file=discord.File(fp=image_binary, filename='image.png'))
    else:
        await message.channel.send('目前沒有正在進行的棋局喔')


async def bot_respond(message):
    global win_rate
    temp = await message.channel.send('我想想怎麼下喔...')
    if is_active:
        history_list = src.leelazGo.history(process)
        think_time = round(1 + 19 * (len(history_list) / 400))
        recommand_positions = src.leelazGo.think(process, think_time)
        win_rate = recommand_positions[0][1]

        if len(history_list) > 100 and float(win_rate) < 25:
            await temp.edit(content='投降啦，你贏了!')
            await end_game(message)
        else:
            if recommand_positions[0][4] == True:
                await temp.edit(content='我想想怎麼下喔...**虛手**~')
                await show_board(message, False, [], [])
            else:
                src.leelazGo.add_move(process, 'W', recommand_positions[0][0])
                await show_board(message, False, [], [])
                await temp.edit(content='我想想怎麼下喔...就這裡了~ **' + recommand_positions[0][0].replace(' ', '')+"** !")
    else:
        await message.channel.send('目前沒有正在進行的棋局喔')


async def score(message):
    if is_active:
        await show_board(message, False, [], [])
        role, score = src.leelazGo.score(process)
        color = ''

        if role == 'White':
            color = '白'
        elif role == 'Black':
            color = '黑'

        if bot_rate == '對局':
            await message.channel.send(color + '+' + str(score) + '目')
        else:
            await message.channel.send(color + '+' + str(score) + '目' + ', 白棋(' + bot_rate + ')勝率 : ' + win_rate + '%')
    else:
        await message.channel.send('目前沒有正在進行的棋局喔')


async def undo_game(message):
    if is_active:
        if src.leelazGo.undo(process):
            if bot_rate == '對局':
                await show_board(message, False, [], [])
            else:
                if src.leelazGo.undo(process):
                    await show_board(message, False, [], [])
                else:
                    await message.channel.send('無法悔棋喔')
        else:
            await message.channel.send('無法悔棋喔')
    else:
        await message.channel.send('目前沒有正在進行的棋局喔')


async def end_game(message):
    global msg, is_active, process
    await message.channel.send('結算棋局')
    if is_active:

        sum, result = src.leelazGo.estimate_score(process)
        await show_board(message, False, [], result)

        sum += 6.5
        if sum > 0:
            await message.channel.send('白勝 ' + str(abs(sum)) + ' 目')
        elif sum == 0:
            await message.channel.send('平局')
        elif sum < 0:
            await message.channel.send('黑勝 ' + str(abs(sum)) + ' 目')

        src.leelazGo.clear_board(process)
        msg = None
        process.kill()
        is_active = False
    else:
        await message.channel.send('目前沒有正在進行的棋局喔')


async def try_save_game(message):
    if is_active:
        await save_game(message)

    else:
        await message.channel.send('目前沒有正在進行的棋局喔')


async def try_load_game(message):
    if is_active:
        await confirm_save_button(message)

    else:
        await load_game(message)
load_message = None


async def confirm_save_button(message):
    global load_message
    yes_button = Button(label="確認", style=discord.ButtonStyle.red)
    no_button = Button(label="取消", style=discord.ButtonStyle.gray)
    view = View()
    view.add_item(yes_button)
    view.add_item(no_button)

    async def yes_button_click(interaction):
        await interaction.response.edit_message(content="讀檔中...", view=None)
        await load_game(message)
    yes_button.callback = yes_button_click

    async def no_button_click(interaction):
        await interaction.message.delete()
    no_button.callback = no_button_click

    await message.delete()
    load_message = await message.channel.send('目前有正在進行的棋局，如果繼續讀檔，該用戶的棋局將會遺失，是否繼續進行？', view=view)


async def load_game(message):
    if is_active:
        await message.channel.send('進度')

    else:
        await message.channel.send('目前沒有正在進行的棋局喔')


async def save_game(message):
    if is_active:
        await message.channel.send('進度')

    else:
        await message.channel.send('目前沒有正在進行的棋局喔')
