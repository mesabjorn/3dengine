import tkinter as tk
import time
import math
# import datetime
import functools
from copy import deepcopy, copy

# inspired on the cpp tutorail from https://www.youtube.com/watch?v=ih20l3pJoeU
from veclib import vec3d, mat4x4, triangle, mesh, rgbToHex, matmatmul, matPointAt, matQuickInverse, mulVecMat, triangleClipAgainstPlane, makeMatRotationX, makeMatRotationY, makeMatRotationZ, makeMatTranslation, dot, cross, makeMatProjection, vec_add, vec_sub, vec_mul, vec_div, vec_len, vec_normalize, makeMatIdentity, sort_triangles_by_z

from player import Player, SceneObject

# CAMERA_INIT = vec3d(60.0, -16, 25.0)


class Engine(tk.Canvas):
    def __init__(self, width=800, height=600):
        super().__init__(width=800, height=600, background="black", highlightthickness=0)
        self.width = width
        self.height = height
        self.aspectratio = self.height/self.width

        # half width and height
        self.hWidth = width*0.5
        self.hHeight = height*0.5

        # self.img = PhotoImage(width=width, height=height)
        # self.create_image((width/2, height/2),
        #                   image=self.img, state="normal")

        # self.ZBuffer = Zbuffer(width, height)

        self.tstart = time.perf_counter()

        # self.vCamera = CAMERA_INIT
        # self.vLookDir = vec3d(0.0, 0.0, 0.0)

        # self.yaw = 0.0
        # self.pitch = 0.0

        self.Player = Player(None, (60, -20, 25))
        self.Player.Camera.setup_viewport(self.aspectratio)

        self.vPointLight = vec3d(-6, -15.0, -50)

        # self.fillDetail = 5     # scanline resolution

        self.text_fps_id = self.create_text(
            50, 10, text=f"Press enter key to start", anchor="w", fill="#fff", font=("TKDefaultFont", 15))

        # right facing snake, 3 body elements, 20px width
        self.bind_all("<Key>", self.on_key_press)
        self.bind("<Motion>", self.on_motion)

        # self.matRotZ = mat4x4()
        # self.matRotX = mat4x4()
        self.scene_objects = []

        # self.after(GAME_SPEED, self.perform_actions)

    def on_motion(self, event):
        # handle mouse movements
        x, y = event.x, event.y
        # print(f"{x},{y}")

    def drawline(self, x1, y1, x2, y2, **kwargs):
        self.create_line(x1, y1, x2, y2, **kwargs)

    def drawtriangle(self, tri: triangle, **kwargs):
        # draw a triangle in clockwise fashion
        # each triangle has 3 vertices
        self.drawline(tri.vertices[0].x, tri.vertices[0].y,
                      tri.vertices[1].x, tri.vertices[1].y, **kwargs)
        self.drawline(tri.vertices[1].x, tri.vertices[1].y,
                      tri.vertices[2].x, tri.vertices[2].y, **kwargs)
        self.drawline(tri.vertices[2].x, tri.vertices[2].y,
                      tri.vertices[0].x, tri.vertices[0].y, **kwargs)

    def fillBottomFlatTriangle(self, v1, v2, v3, **kwargs):
        # v1 = tri.vertices[0]
        # v2 = tri.vertices[1]
        # v3 = tri.vertices[2]

        f = self.fillDetail

        invSlope1 = f*(v3.x - v2.x) / (v3.y-v2.y)
        invSlope2 = f*(v3.x - v1.x) / (v3.y-v1.y)

        curx1 = v3.x
        curx2 = v3.x
        scanlineY = v3.y
        while(scanlineY <= v1.y):
            self.drawline(curx1, scanlineY, curx2,
                          scanlineY, width=f, **kwargs)

            curx1 += invSlope1
            curx2 += invSlope2
            scanlineY += f

    def fillTopFlatTriangle(self, v1, v2, v3, **kwargs):
        f = self.fillDetail
        invSlope1 = f*(v1.x - v2.x) / (v1.y-v2.y)
        invSlope2 = f*(v1.x - v3.x) / (v1.y-v3.y)

        curx1 = v1.x
        curx2 = v1.x
        scanlineY = v1.y
        while(scanlineY >= v3.y):
            self.drawline(curx1, scanlineY, curx2,
                          scanlineY, width=f, **kwargs)

            curx1 -= invSlope1
            curx2 -= invSlope2
            scanlineY -= f

    def fillTriangle_new(self, tri, **kwargs):
        v3, v2, v1 = sorted(tri.vertices, key=lambda v: v.y, reverse=False)

        # genericcase!
        v4 = vec3d(v3.x+(v2.y-v3.y)/(v1.y-v3.y)*(v1.x-v3.x), v2.y, 0)
        self.fillTopFlatTriangle(v1, v2, v4,  **kwargs)
        self.fillBottomFlatTriangle(v2, v4, v3,  **kwargs)

    def fillTriangle(self, tri):
        steps = 20

        # sort vertices by y position
        ys = sorted(tri.vertices, key=lambda v: v.y, reverse=True)

        p1 = ys[0]
        p2 = ys[1]
        p3 = ys[2]
        Q = p2.y

        x0 = p1.x
        y0 = p1.y
        for i in range(1, steps+1, 1):
            t = i/steps
            # print(t)
            ax = x0+((p3.x-p1.x)*t)
            ay = y0+((p3.y-p1.y)*t)

            bx = x0+((p2.x-p1.x)*t)
            by = y0+((p2.y-p1.y)*t)

            self.create_line(ax, ay, bx, by, fill="#FFF", width=5)
            # print(by)
            # print(
            #     f"board.create_line({int(ax)},{int(ay)},{int(bx)},{int(by)}, fill='white')")
            # if(ay < Q):
            #     break

    def drawmeshes(self):
        for scene_object in self.scene_objects:
            scene_object.update(time.perf_counter())
            scene_object.draw(time.perf_counter(), self)
            # self.drawmesh(scene_object)

    def drawmesh(self, scene_object: SceneObject):
        trianglesToRaster = []
        m = scene_object.mesh
        for t in m.tris:
            triTransformed = triangle([0, 0, 0], [0, 0, 0], [0, 0, 0])

            triTransformed.vertices[0] = mulVecMat(
                t.vertices[0], self.matWorld)
            triTransformed.vertices[1] = mulVecMat(
                t.vertices[1], self.matWorld)
            triTransformed.vertices[2] = mulVecMat(
                t.vertices[2], self.matWorld)

            # use each sceneobjects cusom translation
            triTransformed.vertices[0] = vec_add(
                triTransformed.vertices[0], scene_object.vPos)
            triTransformed.vertices[1] = vec_add(
                triTransformed.vertices[1], scene_object.vPos)
            triTransformed.vertices[2] = vec_add(
                triTransformed.vertices[2], scene_object.vPos)

            if(scene_object.rotate):
                rotZ = makeMatRotationY(time.perf_counter())
                triTransformed.vertices[0] = mulVecMat(
                    triTransformed.vertices[0], rotZ)
                triTransformed.vertices[1] = mulVecMat(
                    triTransformed.vertices[1], rotZ)
                triTransformed.vertices[2] = mulVecMat(
                    triTransformed.vertices[2], rotZ)

            # triRotZ = triangle(
            #     tout0, tout1, tout2)

            # tout0 = mulVecMat(triRotZ.vertices[0], self.matRotX)
            # tout1 = mulVecMat(triRotZ.vertices[1], self.matRotX)
            # tout2 = mulVecMat(triRotZ.vertices[2], self.matRotX)

            # triRotZX = triangle(
            #     tout0, tout1, tout2)

            # triRotZX.vertices[0].z += 20.0
            # triRotZX.vertices[1].z += 20.0
            # triRotZX.vertices[2].z += 20.0

            # get two edges on the triangle
            line1 = vec_sub(
                triTransformed.vertices[1], triTransformed.vertices[0])
            line2 = vec_sub(
                triTransformed.vertices[2], triTransformed.vertices[0])

            # cross product between line 1 and 2 => orthogonal vector
            normal = cross(line1, line2)
            normal = vec_normalize(normal)

            # get ray from triangle to camera
            vCameraRay = vec_sub(
                triTransformed.vertices[0], self.Player.Camera.vPos)

            # check if this face should be visualized
            if(dot(normal, vCameraRay) < 0.0):
                triProjected = triangle((0, 0, 0), (0, 0, 0), (0, 0, 0))
                # each triangle has 3 vertices
                # transform vertex coords to proj coords 3d->2d

                # compute correct color
                dp = dot(normal, vec_normalize(self.vPointLight))
                # dp = 1
                color = copy(m.ambientColor)

                color = vec_mul(color, dp)
                color.x = int(color.x)   # r channel
                color.y = int(color.y)   # g channel
                color.z = int(color.z)   # b channel

                # color.x = max(color.x, 0)
                # color.y = max(color.y, 0)
                # color.z = max(color.z, 0)

                triViewed = triangle((0, 0, 0), (0, 0, 0), (0, 0, 0))

                triViewed.vertices[0] = mulVecMat(
                    triTransformed.vertices[0], self.Player.Camera.matView)
                triViewed.vertices[1] = mulVecMat(
                    triTransformed.vertices[1], self.Player.Camera.matView)
                triViewed.vertices[2] = mulVecMat(
                    triTransformed.vertices[2], self.Player.Camera.matView)

                triViewed.color = color

                nClippedTris = triangleClipAgainstPlane(
                    vec3d(0, 0, .1), vec3d(0, 0, 1.0), triViewed)

                clippedTriangles = []
                if(nClippedTris[0] >= 1):
                    clippedTriangles = nClippedTris[1:]
                # print(f"len clipped tris:{nClippedTris[0]}")

                for clippedTriangle in clippedTriangles:
                    # project triangle to 2d space
                    triProjected = triangle((0, 0, 0), (0, 0, 0), (0, 0, 0))

                    triProjected.vertices[0] = mulVecMat(
                        clippedTriangle.vertices[0], self.Player.Camera.matProj)
                    triProjected.vertices[1] = mulVecMat(
                        clippedTriangle.vertices[1], self.Player.Camera.matProj)
                    triProjected.vertices[2] = mulVecMat(
                        clippedTriangle.vertices[2], self.Player.Camera.matProj)

                    triProjected.vertices[0] = vec_div(
                        triProjected.vertices[0], triProjected.vertices[0].w)
                    triProjected.vertices[1] = vec_div(
                        triProjected.vertices[1], triProjected.vertices[1].w)
                    triProjected.vertices[2] = vec_div(
                        triProjected.vertices[2], triProjected.vertices[2].w)

                    triProjected.vertices[0].x *= -1
                    triProjected.vertices[0].y *= -1
                    triProjected.vertices[1].x *= -1
                    triProjected.vertices[1].y *= -1
                    triProjected.vertices[2].x *= -1
                    triProjected.vertices[2].y *= -1

                    # put it into view (offset it into x,y direction)
                    vOffsetView = vec3d(1, 1, 0)
                    triProjected.vertices[0] = vec_add(
                        triProjected.vertices[0], vOffsetView)
                    triProjected.vertices[1] = vec_add(
                        triProjected.vertices[1], vOffsetView)
                    triProjected.vertices[2] = vec_add(
                        triProjected.vertices[2], vOffsetView)

                    # scale into view
                    triProjected.vertices[0].x *= self.hWidth
                    triProjected.vertices[0].y *= self.hHeight
                    triProjected.vertices[1].x *= self.hWidth
                    triProjected.vertices[1].y *= self.hHeight
                    triProjected.vertices[2].x *= self.hWidth
                    triProjected.vertices[2].y *= self.hHeight

                    # triProjected.color = copy(triViewed.color)
                    triProjected.color = clippedTriangle.color

                    trianglesToRaster.append(triProjected)

        # sort triangles in z axis for painters rendering
        trianglesToRaster = sorted(
            trianglesToRaster, key=functools.cmp_to_key(sort_triangles_by_z))

        for t in trianglesToRaster:
            listTriangles = []
            listTriangles.append(t)
            nNewTriangles = 1
            for p in range(0, 4):
                nTrisToAdd = 0
                while nNewTriangles > 0:
                    test = listTriangles[0]
                    del listTriangles[0]
                    nNewTriangles -= 1

                    if(p == 0):
                        nTrisToAdd = triangleClipAgainstPlane(
                            vec3d(0, 0, 0), vec3d(0, 1, 0), test)
                    elif(p == 1):
                        nTrisToAdd = triangleClipAgainstPlane(
                            vec3d(0, self.height-1, 0), vec3d(0, -1, 0), test)
                    elif(p == 2):
                        nTrisToAdd = triangleClipAgainstPlane(
                            vec3d(0, 0, 0), vec3d(1, 0, 0), test)
                    elif(p == 3):
                        nTrisToAdd = triangleClipAgainstPlane(
                            vec3d(self.width-1, 0, 0), vec3d(-1, 0, 0), test)

                    if(nTrisToAdd[0] >= 1):
                        for n in nTrisToAdd[1:]:
                            listTriangles.append(n)
                nNewTriangles = len(listTriangles)

            for t in listTriangles:
                # t.color = vec3d(255, 255, 255)
                self.create_polygon(t.vertices[0].x, t.vertices[0].y, t.vertices[1].x,
                                    t.vertices[1].y, t.vertices[2].x, t.vertices[2].y, fill=rgbToHex(t.color), tag="triangle")

                # self.drawtriangle(t, fill="white")      # enable wireframe mode

        # def setup_viewport(self):

    #     fNear = 0.1
    #     fFar = 1000.0
    #     fFov = 90.0         # degrees FOV
    #     self.matProj = makeMatProjection(fFov, self.aspectratio, fNear, fFar)

    def perform_actions(self):
        # self.draw()
        t1 = time.perf_counter()
        self.delete(tk.ALL)
        theta = 0  # t1*0.5

        # self.matRotZ = makeMatRotationZ(theta)
        # self.matRotX = makeMatRotationX(theta)
        # self.matRotY = makeMatRotationY(theta)
        # self.matTrans = makeMatTranslation(0, 0, 0)

        self.matWorld = makeMatIdentity()
        # self.matWorld = matmatmul(self.matRotZ, self.matRotX)
        # self.matWorld = matmatmul(self.matWorld, self.matTrans)

        self.Player.Camera.setCamera()
        self.drawmeshes()

        t2 = time.perf_counter()-t1             # frame draw time
        self.text_fps_id = self.create_text(
            0, 10, text=f"{1/t2:3.0f} fps", anchor="w", fill="#fff", font=("TKDefaultFont", 12))
        self.camerapostext = self.create_text(
            0, 20, text=f"camera (xyz)= {self.Player.Camera.vPos.x}, {self.Player.Camera.vPos.y}, {self.Player.Camera.vPos.z}", anchor="w", fill="#fff", font=("TKDefaultFont", 10))
        self.camerapostext = self.create_text(
            0, 30, text=f"camera (pitch,yaw,roll) = {self.Player.Camera.pitch:.2f}, {self.Player.Camera.yaw:.2f}, {0}", anchor="w", fill="#fff", font=("TKDefaultFont", 10))

        # self.vPointLight.x += math.sin(t1)
        # self.vPointLight.y += math.cos(t1)
        # self.after(max(1, int(t2*1000)), self.perform_actions)
        self.after(40, self.perform_actions)

    def on_key_press(self, e):
        # model = self.create_cube()
        # print(e)
        if(e.keycode == 13):

            # S = SceneObject(0, 0, -5, "lowpolylevel.obj")
            S = SceneObject("lowpolylevel.obj", (0, 0, -5))
            # model.loadmodelfromfile("./engine3d/models/lowpolylevel.obj")
            # model.ambientColor = vec3d(64, 224, 208)

            self.addModelToScene(S)

            S2 = SceneObject("box.obj", (0, -5, 0), vScale=(5, 5, 5))
            S2.rotate = True
            S2.myupdatefunction = SceneObject.bounce
            S2.ambientColor = vec3d(64, 224, 208)
            self.addModelToScene(S2)

            S3 = SceneObject("box.obj", (5, -5, 0), vScale=(1, 1, 1))
            self.addModelToScene(S3)

            # model = mesh()
            # model.loadmodelfromfile("./engine3d/models/box.obj")
            # model.ambientColor = vec3d(64, 224, 208)
            # # model.ambientColor = vec3d(255, 255, 255)
            # self.addModelToScene(model)

            return

        vForward = vec_mul(self.Player.Camera.vLookDir, 1)

        if(e.keycode == 40):
            # key down
            self.Player.Camera.vPos.y += 1
        elif(e.keycode == 38):
            # key up
            self.Player.Camera.vPos.y -= 1
        elif(e.keycode == 39):
            # key right
            self.Player.Camera.vPos.x += 1
        elif(e.keycode == 37):
            # key left
            self.Player.Camera.vPos.x -= 1
        elif(e.keycode == 68):
            # D
            self.Player.Camera.yaw -= .1
            # self.yaw %= 6.28
            if(self.Player.Camera.yaw <= 0):
                self.Player.Camera.yaw += 6.3

        elif(e.keycode == 65):
            # A
            self.Player.Camera.yaw += .1
            # self.yaw %= 6.28
            if(self.Player.Camera.yaw >= 6.3):
                self.Player.Camera.yaw -= 6.3

        elif(e.keycode == 87):
            # W
            self.Player.Camera.vPos = vec_add(
                self.Player.Camera.vPos, vForward)
        elif(e.keycode == 83):
            # S
            self.Player.Camera.vPos = vec_sub(
                self.Player.Camera.vPos, vForward)
        elif(e.keycode == 33):
            # pgup
            self.Player.Camera.pitch += .1
            # self.pitch %= 6.28
        elif(e.keycode == 34):
            # pgdown (tilt camera)
            self.Player.Camera.pitch -= .1
            # self.pitch %= 6.28
        elif(e.char == "r"):
            # reset
            self.Player.Camera.vPos = self.Player.vPos
            self.Player.Camera.yaw = 0
            self.Player.Camera.pitch = 0
        elif(e.keycode == 67):
            # c
            self.Player.Camera = self.Player.Camera2
            self.Player.Camera.setup_viewport(self.aspectratio)
            self.Player.Camera.yaw = 5.5
            self.Player.Camera.pitch = -0.6
            # self.addmodeltoscene(model)
            # for x in range(4 * self.width):
            #     y = int(self.height/2 + self.height/4 * math.sin(x/80.0))
            #     self.img.put("#ffffff", (x//4, y))

    def addModelToScene(self, scene_object: SceneObject) -> None:
        self.scene_objects.append(scene_object)
        self.perform_actions()

    def create_cube(self):

        # south (facing us)
        t0 = triangle((0.0, 0.0, 0.0), (0.0, 1.0, 0.0), (1.0, 1.0, 0.0))
        t1 = triangle((0.0, 0.0, 0.0), (1.0, 1.0, 0.0), (1.0, 0.0, 0.0))

        # east
        t2 = triangle((1.0, 0.0, 0.0), (1.0, 1.0, 0.0), (1.0, 1.0, 1.0))
        t3 = triangle((1.0, 0.0, 0.0), (1.0, 1.0, 1.0), (1.0, 0.0, 1.0))

        # north
        t4 = triangle((1.0, 0.0, 1.0), (1.0, 1.0, 1.0), (0.0, 1.0, 1.0))
        t5 = triangle((1.0, 0.0, 1.0), (0.0, 1.0, 1.0), (0.0, 0.0, 1.0))

        # west
        t6 = triangle((0.0, 0.0, 1.0), (0.0, 1.0, 1.0), (0.0, 1.0, 0.0))
        t7 = triangle((0.0, 0.0, 1.0), (0.0, 1.0, 0.0), (0.0, 0.0, 0.0))

        # top
        t8 = triangle((0.0, 1.0, 0.0), (0.0, 1.0, 1.0), (1.0, 1.0, 1.0))
        t9 = triangle((0.0, 1.0, 0.0), (1.0, 1.0, 1.0), (1.0, 1.0, 0.0))

        # bottom
        t10 = triangle((1.0, 0.0, 1.0), (0.0, 0.0, 1.0), (0.0, 0.0, 0.0))
        t11 = triangle((1.0, 0.0, 1.0), (0.0, 0.0, 0.0), (1.0, 0.0, 0.0))

        # print(self.matProj.mat)
        return mesh(t0, t1, t2, t3, t4, t5, t6, t7, t8, t9, t10, t11)
        # self.perform_actions()


root = tk.Tk()
root.title("3d engine")
root.resizable(False, False)

board = Engine()
board.pack()

# board.drawline(100, 100, 200, 200)

# board.create_line(100, 100, 200, 200, arrow=tk.LAST, fill="#FFF")

# flat top
# a = (100, 200, 100)
# b = (50, 100, 100)
# c = (150, 100, 100)
# t = triangle(a, b, c)
# board.drawtriangle(t)
# board.fillTriangle_new(t)

# a = (300, 200, 100)
# b = (400, 100, 100)
# c = (500, 250, 100)
# t = triangle(a, b, c)
# board.drawtriangle(t)
# board.fillTriangle_new(t)

# a = (400, 400, 100)
# b = (450, 200, 100)
# c = (700, 100, 100)
# t = triangle(a, b, c)
# board.drawtriangle(t)
# board.fillTriangle_new(t)

root.mainloop()
