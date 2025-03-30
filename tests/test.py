"""from lib.planner import Planning


p = Planning(expired_plan_timeout=0)
p.add_plan('hoop_dunkgz', 'find_videos', 1)
p.execute()
print(p)
"""
"""
from lib.editor.io.topaz.listener import run_watch_folder


run_watch_folder()

"""




"""from lib.analysts.video import VideoAnalyst


import asyncio


async def do():
    for i in range(60):
        print('Doing something')
        await asyncio.sleep(1)
        print('Back here')


async def analyze():
    vm = VideoAnalyst()
    vm.login()
    vm.start_chat()
    print(await vm.analyze_async("content_saved//downloaded//stock_test//TikTok{{{7398261979502103841.mp4"))


async def main():
    await asyncio.gather(analyze(), do())


asyncio.run(main())
"""
"""from lib.creator.myvideo import MyVideo


mv = MyVideo(auto_save=True)
print(mv.__dict__)"""


"""from lib.editor.commandbuilder import CommandBuilder


c1 = {'clip_paths': ['-i', 'C://Users//Emilien//Bureau//testtsts4.mp4'], 'output_video_path': ['-o', 'content_created//FINAL//28-11-2024_23-53-58//#fyp.mov'], 'audio_path': ['-a'], 'concatenate_mode': ['-cm', 'cutR_extendR_fit'], 'timeline_audio_sync': ['-ta', '9.0,11.0'], 'shuf': ['-sh', 'True'], 'transitions': ['-tr'], 'effects': ['-ef'], 'fps': ['-f', 'None'], 'scale': ['-sc', '1'], 'topaz_preset': ['-z', 'None'], 'keep_clip_audios': ['-ka', 'True'], 'preview': ['-p']} 

c2 = {'clip_paths': ['-i', 'C://Users//Emilien//Bureau//testtsts4.mp4'], 'output_video_path': ['-o', 'content_created//FINAL//28-11-2024_23-30-24//#fyp.mov'], 'audio_path': ['-a'], 'concatenate_mode': ['-cm', 'cutR_extendR_fit'], 'timeline_audio_sync': ['-ta', '9.0,11.0'], 'shuf': ['-sh', 'True'], 'transitions': ['-tr'], 'effects': ['-ef'], 'fps': ['-f', 'None'], 'scale': ['-sc', '1'], 'topaz_preset': ['-z', 'None'], 'keep_clip_audios': ['-ka', 'True'], 'preview': ['-p']}

print(CommandBuilder.is_same_command(c1, c2))


"""

#from lib.creator.myvideo import MyVideo


"""vs = MyVideo.all_myvideos
print('/n'.join([str(myvideo.command_builder._command) for myvideo in vs]))
"""
"""from atexit import register, unregister

x = lambda: print('h')
register(x)
unregister(lambda: print('h'))"""


"""from lib.editor.commandbuilder import CommandBuilder

c = '''
python editor.py -i C:/Users/Emilien/Bureau/tiktok{{{_cr7tlb_{{{7427012631904505118.mp4 -cm cutR_extendR_fit -ta 0.0,2.0 -sh False -ef t:t=test~w=0.8~d=None~p=center~j=center~m=35 -f None -sc 1 -z None -ka True -q LQ -ae aecompcc.jsx:ffxPath=C:/Users/Emilien/Documents/Adobe/After Effects 2024/User Presets/Irvin Cold CC.ffx -o C:/Users/Emilien/Bureau/output1.mp4
'''
c = ['python', 'editor.py', '-i', 'C:/Users/Emilien/Bureau/tiktok{{{_cr7tlb_{{{7427012631904505118.mp4', '-cm', 'cutR_extendR_fit', '-ta', '0.0,2.0', '-sh', 'False', '-ef', 't:t=test~w=0.8~d=None~p=center~j=center~m=35', '-f', 'None', '-sc', '1', '-z', 'None', '-ka', 'True', '-q', 'LQ', '-o', 'C:/Users/Emilien/Bureau/output1.mov']

cb = CommandBuilder.from_command(c)

cb.add_argument('aecompcc.jsx', {'ffxPath': 'C:/Users/Emilien/Documents/Adobe/After Effects 2024/User Presets/Irvin Cold CC.ffx'})
cb.add_argument('ae_export_quality', 'HQ')

cb.execute(print_cmd=True)"""

"""from lib.dataproc import UListVideoDatas

UListVideoDatas.recover_data()
exit()
videos = UListVideoDatas.load()
videos[:2].remove(update_copy=False)


"""

if __name__ == "__main__":
    from lib.planning import Planning
    p = Planning(expired_plan_timeout=0)
    p.add_plan(
        account_name='nikita_rzm_space',
        task_name='editing',
        exec_func_name='main',
        goal_value=11)
    p.execute()
    print(p)

