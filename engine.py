from aiortc import VideoStreamTrack
import numpy
import cv2
import math
from av import VideoFrame
import backend as back

db = back.firestore.AsyncClient()


class FlagVideoStreamTrack(VideoStreamTrack):
    def __init__(self):
        super().__init__()
        self.counter = 0
        height, width = 480, 640

        #make the flag
        data_bgr = numpy.hstack(
            [
                self._create_rectangle(
                    width=213, height=480, color=(255, 0, 0)
                ),
                self._create_rectangle(
                    width = 214, height=480, color=(255, 255, 255)
                ),
                self._create_rectangle(width=213, height=480, color=(0, 0, 255)),

            ]
        )


        #render the flag
        M = numpy.float32([[0.5, 0, width / 4], [0, 0.5, height / 4]])
        data_bgr = cv2.warpAffine(data_bgr, M, (width, height))
        omega = 2 * math.pi / height

        id_x = numpy.tile(numpy.array(range(width), dtype=numpy.float32), (height, 1))
        id_y = numpy.tile(
            numpy.array(range(height), dtype=numpy.float32), (width, 1)
        ).transpose()
        
        self.frames = []
        for k in range(30):
            phase = 2 * k * math.pi / 30
            map_x = id_x + 10 * numpy.cos(omega * id_x + phase)
            map_y = id_y + 10 * numpy.sin(omega * id_x + phase)
            self.frames.append(
                VideoFrame.from_ndarray(
                    cv2.remap(data_bgr, map_x, map_y, cv2.INTER_LINEAR), format="bgr24"
                )
        )
    

    async def recv(self):
        pts, time_base = await self.next_timestamp()

        frame = self.frames[self.counter % 30]
        frame.pts = pts
        frame.time_base = time_base
        self.counter += 1
        return frame

    def _create_rectangle(self, width, height, color):
        data_bgr = numpy.zeros((height, width, 3), numpy.uint8)
        data_bgr[:, :] = color
        return data_bgr

async def run(pc, player, recorder, signaling, role):
    def add_tracks():
        if player and player.audio:
            pc.addTrack(player.audio)
        if player and player.video:
            pc.addTrack(player.video)
        else:
            pc.addTrack(FlagVideoStreamTrack())
    
    @pc.on("track")
    def on_track(track):
        print("Recieving %s" % track.kind)
        recorder.addTrack(track)

    await signaling.connect()

    if role == "offer":
        add_tracks()
        await pc.setLocalDescription(await pc.createOffer())
        await signaling.send(pc.localDescription)
        #await addData(str(pc.localDescription))
        db_ref = db.collection("users")
        offer = await back.firebase_to_string(db_ref)
        print(offer)




    while True:
        obj = await signaling.receive()

        #recieved response
        if isinstance(obj, RTCSessionDescription):
            await pc.setRemoteDescription(obj)
            await recorder.start()

            if obj.type == "offer":
                add_tracks()
                await pc.setLocalDescription(await pc.createAnswer())
                await signaling.send(pc.localDescription)
            elif isinstance(obj, RTCIceCandidate):
                await pc.addIceCandidate(obj)
            elif obj is BYE:
                print("Exiting")
                break
