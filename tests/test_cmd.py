print(input('link:\n').replace(r"\u002F", "/"))


"""
ffprobe -v quiet -print_format json -show_format -show_streams -print_format json "C:\Users\Emilien\Downloads\clue\model.mp4"

ffprobe -v quiet -print_format json -show_format -show_streams -print_format json "C:\Users\Emilien\Desktop\new_test\out_crf25.mp4"

ffprobe -v quiet -print_format json -show_format -show_streams -print_format json "C:\Users\Emilien\Desktop\Python\projects\content_creator\content_automation\core\content_created\FINAL\03-03-2025_22-32-52-68\instagram_03-03-2025_22-32-52-68.mp4"

ffprobe -v quiet -print_format json -show_format -show_streams -print_format json "C:\Users\Emilien\Desktop\test_export_hd.mp4"

"""
"""-vf "scale=1920:1088,setsar=1" ^
-bsf:v remove_extra ^"""

"""
ffmpeg -i "C:\Users\Emilien\Desktop\new_test\Comp 3.mov" ^
-map 0:v -map 0:a ^
-movflags frag_keyframe+empty_moov+delay_moov+use_metadata_tags ^
-map_metadata -1 ^
-metadata:s:v handler_name="VideoHandler" ^
-metadata:s:a handler_name="SoundHandler" ^
-metadata encoder="Lavf57.71.100" ^
-c:v libx265 -profile:v main -tag:v hvc1 -pix_fmt yuv420p ^
-color_range tv -color_primaries bt709 -color_trc bt709 -colorspace bt709 ^
-b:v 10725k -minrate 10725k -maxrate 10725k -bufsize 21450k ^
-r 358000000/5966667 -refs 1 -x265-params "level=5.1" -bf 0 ^
-video_track_timescale 1000000 ^
-preset medium ^
-c:a aac -b:a 125k -ac 2 -ar 44100 ^
-metadata creation_time="2025-02-17T19:54:13Z" ^
-metadata bitrate="9676800" -metadata mdat_pos="28" ^
-metadata maxrate="0" -metadata te_is_reencode="1" ^
-metadata moov_pos="24276685" -metadata writerType="-1" ^
-metadata minor_version="512" ^
-metadata source="5" -metadata Hw="1" ^
-metadata major_brand="qt  " -metadata compatible_brands="qt  " ^
-disposition:v default -disposition:a default ^
-map_chapters -1 ^
"C:\Users\Emilien\Desktop\new_test\out.mp4"

"""


"""
ffmpeg -i "C:\Users\Emilien\Desktop\new_test\Comp 1.mov" ^
-map 0:v -map 0:a ^
-map_metadata -1 ^
-c:v libx265 -profile:v main -tag:v hvc1 -pix_fmt yuv420p ^
-color_range tv -color_primaries bt709 -color_trc bt709 -colorspace bt709 ^
-crf 25 -refs 1 -x265-params "level=5.1" -bf 2 ^
-preset veryslow ^
-c:a aac -b:a 125k -ac 2 -ar 44100 ^
"C:\Users\Emilien\Desktop\new_test\out_crf25.mp4"

"""