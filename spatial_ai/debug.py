import time
from depthai_sdk import OakCamera, RecordType

with OakCamera() as oak:
    color = oak.create_camera('color', resolution='1080P', fps=30)
    # color = oak.create_camera('color', resolution='1080P', fps=20, encode='H265')
    # left = oak.create_camera('left', resolution='800p', fps=20, encode='H265')
    # right = oak.create_camera('right', resolution='800p', fps=20, encode='H265')

    # Synchronize & save all (encoded) streams
    oak.record([color.out.encoded], './', RecordType.VIDEO)
    # Show color stream
    # oak.visualize([color.out.camera], scale=2/3, fps=True)

    oak.start()
    start_time = time.monotonic()
    last_print_time = 5
    while oak.running():
        running_time = time.monotonic() - start_time
        if running_time > last_print_time:
            last_print_time+=5
            print(f"  Running time: {running_time}")
        if running_time > 10:
            break
        oak.poll()
