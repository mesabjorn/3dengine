import tkinter as tk
import time
import math

# inspired on the cpp tutorail from https://www.youtube.com/watch?v=ih20l3pJoeU


MOVE_INCREMENT = 20
moves_per_second = 15
GAME_SPEED = 1000//moves_per_second


class vec3d:
    def __init__(self, x, y, z) -> None:
        self.x = x
        self.y = y
        self.z = z

    def aslist(self):
        return [self.x, self.y, self.z]


class triangle:
    def __init__(self, p1, p2, p3) -> None:
        if(type(p1) == vec3d):
            self.vertices = [p1, p2, p3]
        else:
            self.vertices = [vec3d(*p1), vec3d(*p2), vec3d(*p3)]


class mesh:
    def __init__(self, *args):
        self.tris = [*args]
        print(self.tris)


class mat4x4:
    def __init__(self):
        self.mat = [[0.0, 0.0, 0.0, 0.0], [0.0, 0.0, 0.0, 0.0],
                    [0.0, 0.0, 0.0, 0.0], [0.0, 0.0, 0.0, 0.0]]


def MultiplyMatrixVector(i, matrix):
    output = vec3d(0.0, 0.0, 0.0)
    m = matrix.mat
    output.x = i.x * m[0][0] + i.y * m[1][0] + i.z*m[2][0] + m[3][0]
    output.y = i.x * m[0][1] + i.y * m[1][1] + i.z*m[2][1] + m[3][1]
    output.z = i.x * m[0][2] + i.y * m[1][2] + i.z*m[2][2] + m[3][2]

    w = i.x * m[0][3] + i.y * m[1][3] + i.z * m[2][3] + m[3][3]

    if(w != 0):
        output.x /= w
        output.y /= w
        output.z /= w

    return output


class Engine(tk.Canvas):
    def __init__(self, width=800, height=600):
        super().__init__(width=800, height=600, background="black", highlightthickness=0)
        self.width = width
        self.height = height
        self.aspectratio = self.height/self.width

        self.tstart = time.time()

        self.vCamera = vec3d(0.0, 0.0, 0.0)
        self.vPointLight = vec3d(0.0, 0.0, -1.0)

        self.fillDetail = 1

        self.text_fps_id = self.create_text(
            50, 10, text=f"Press any key", anchor="w", fill="#fff", font=("TKDefaultFont", 15))
        # right facing snake, 3 body elements, 20px width
        self.bind_all("<Key>", self.on_key_press)

        # self.after(GAME_SPEED, self.perform_actions)

    def drawline(self, x1, y1, x2, y2, **kwargs):
        self.create_line(x1, y1, x2, y2, **kwargs)

    def drawtriangle(self, tri, **kwargs):
        # draw a triangle in clockwise fashion
        # each triangle has 3 vertices
        l = self.drawline(tri.vertices[0].x, tri.vertices[0].y,
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
                          scanlineY, width=5, **kwargs)

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
                          scanlineY, width=5, **kwargs)

            curx1 -= invSlope1
            curx2 -= invSlope2
            scanlineY -= f

    def fillTriangle_new(self, tri, **kwargs):
        ys = sorted(tri.vertices, key=lambda v: v.y, reverse=False)
        v1 = ys[2]
        v2 = ys[1]
        v3 = ys[0]

        # if(v2.y == v3.y):
        #     self.fillTopFlatTriangle(v1, v2, v3)
        # elif(v1.y == v2.y):
        #     self.fillBottomFlatTriangle(v1, v2, v3)
        # else:
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
            print(
                f"board.create_line({int(ax)},{int(ay)},{int(bx)},{int(by)}, fill='white')")
            # if(ay < Q):
            #     break

    def drawmesh(self, m):
        # for t in m.tris:
        for i in range(0, len(m.tris)):
            t = m.tris[i]

            tout0 = MultiplyMatrixVector(t.vertices[0], self.matRotZ)
            tout1 = MultiplyMatrixVector(t.vertices[1], self.matRotZ)
            tout2 = MultiplyMatrixVector(t.vertices[2], self.matRotZ)

            # triRotZ = triangle(
            #     tout0.aslist(), tout1.aslist(), tout2.aslist())

            triRotZ = triangle(
                tout0, tout1, tout2)

            tout0 = MultiplyMatrixVector(triRotZ.vertices[0], self.matRotX)
            tout1 = MultiplyMatrixVector(triRotZ.vertices[1], self.matRotX)
            tout2 = MultiplyMatrixVector(triRotZ.vertices[2], self.matRotX)

            triRotZX = triangle(
                tout0, tout1, tout2)

            triRotZX.vertices[0].z += 3.0
            triRotZX.vertices[1].z += 3.0
            triRotZX.vertices[2].z += 3.0

            # get two lines on the triangle
            line1 = vec3d(triRotZX.vertices[1].x-triRotZX.vertices[0].x,
                          triRotZX.vertices[1].y-triRotZX.vertices[0].y,
                          triRotZX.vertices[1].z-triRotZX.vertices[0].z)

            line2 = vec3d(triRotZX.vertices[2].x-triRotZX.vertices[0].x,
                          triRotZX.vertices[2].y-triRotZX.vertices[0].y,
                          triRotZX.vertices[2].z-triRotZX.vertices[0].z)

            # cross product between line 1 and 2 => orthogonal vector
            normal = vec3d(line1.y*line2.z-line1.z*line2.y,
                           line1.z*line2.x-line1.x*line2.z,
                           line1.x*line2.y-line1.y*line2.x)

            # normalize normal
            l = math.sqrt(normal.x*normal.x+normal.y *
                          normal.y+normal.z*normal.z)

            normal.x /= l
            normal.y /= l
            normal.z /= l

            dotproduct = normal.x*(triRotZX.vertices[0].x - self.vCamera.x) + normal.y * (
                triRotZX.vertices[0].y - self.vCamera.y) + normal.z * (triRotZX.vertices[0].z - self.vCamera.z)
            # if(normal.z < 0):
            # print(dotproduct)
            if(dotproduct < 0.0):
                # each triangle has 3 vertices
                # transform vertex coords to proj coords 3d->2d
                tout0 = MultiplyMatrixVector(
                    triRotZX.vertices[0], self.matProj)
                tout1 = MultiplyMatrixVector(
                    triRotZX.vertices[1], self.matProj)
                tout2 = MultiplyMatrixVector(
                    triRotZX.vertices[2], self.matProj)

                # build a triangle in transformed coords
                triProjected = triangle(
                    tout0, tout1, tout2)

                triProjected.vertices[0].x += 1
                triProjected.vertices[0].y += 1

                triProjected.vertices[1].x += 1
                triProjected.vertices[1].y += 1

                triProjected.vertices[2].x += 1
                triProjected.vertices[2].y += 1

                # scale into view
                triProjected.vertices[0].x *= 0.5*self.width
                triProjected.vertices[0].y *= 0.5*self.height
                triProjected.vertices[1].x *= 0.5*self.width
                triProjected.vertices[1].y *= 0.5*self.height
                triProjected.vertices[2].x *= 0.5*self.width
                triProjected.vertices[2].y *= 0.5*self.height

                # triProjected.vertices[0].y = self.height-triProjected.vertices[0].y
                # triProjected.vertices[1].y = self.height-triProjected.vertices[1].y
                # triProjected.vertices[2].y = self.height-triProjected.vertices[2].y

                l = math.sqrt(self.vPointLight.x*self.vPointLight.x+self.vPointLight.y *
                              self.vPointLight.y+self.vPointLight.z*self.vPointLight.z)
                self.vPointLight.x /= l
                self.vPointLight.y /= l
                self.vPointLight.z /= l

                dp = normal.x*self.vPointLight.x+normal.y * \
                    self.vPointLight.y+normal.z*self.vPointLight.z

                color = vec3d(255, 255, 255)    # red
                color.x = int(dp*color.x)   # r channel
                color.y = int(dp*color.y)   # g channel
                color.z = int(dp*color.z)   # b channel
                # color = vec3d(255, 255, 255)
                # and draw it
                self.fillTriangle_new(
                    triProjected, fill=f"#{color.x:02x}{color.y:02x}{color.z:02x}")
                # self.drawtriangle(triProjected)
                # if(i == 0):
                #     break

    def draw(self):
        pass

    def perform_actions(self):
        # self.draw()
        t1 = time.time()

        self.delete(tk.ALL)

        theta = time.time()-self.tstart

        self.matRotZ = mat4x4()
        self.matRotZ.mat[0][0] = math.cos(theta*0.5)
        self.matRotZ.mat[0][1] = math.sin(theta*0.5)
        self.matRotZ.mat[1][0] = -math.sin(theta*0.5)
        self.matRotZ.mat[1][1] = math.cos(theta*0.5)
        self.matRotZ.mat[2][2] = 1.0
        self.matRotZ.mat[3][3] = 1.0

        self.matRotX = mat4x4()
        self.matRotX.mat[0][0] = 1.0
        self.matRotX.mat[1][1] = math.cos(theta*0.5)
        self.matRotX.mat[1][2] = math.sin(theta*0.5)
        self.matRotX.mat[2][1] = -math.sin(theta*0.5)
        self.matRotX.mat[2][2] = math.cos(theta*0.5)
        self.matRotX.mat[3][3] = 1.0

        self.drawmesh(self.m)
        # self.after(GAME_SPEED, self.perform_actions)
        t2 = time.time()-t1        # frame draw time
        self.text_fps_id = self.create_text(
            0, 10, text=f"fps = {1/t2}", anchor="w", fill="#fff", font=("TKDefaultFont", 15))

        self.after(max(1, t2), self.perform_actions)
        # self.update_idletasks()

    def on_key_press(self, e):
        new_direction = e.keysym
        # self.drawline(100, 100, 200, 200)
        # t = triangle((100, 50), (100, 100), (150, 100))
        # t2 = triangle((100, 50), (150, 100), (150, 50))

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

        fNear = 0.1
        fFar = 1000.0
        fFov = 90.0
        fFovRad = 1.0/math.tan(fFov*0.5/180.0*3.14159)

        self.matProj = mat4x4()
        self.matProj.mat[0][0] = self.aspectratio*fFovRad
        self.matProj.mat[1][1] = fFovRad
        self.matProj.mat[2][2] = fFar/(fFar-fNear)
        self.matProj.mat[3][2] = (-fFar*fNear)/(fFar-fNear)
        self.matProj.mat[2][3] = 1.0
        self.matProj.mat[3][3] = 0.0

        print(self.matProj.mat)
        self.m = mesh(t0, t1, t2, t3, t4, t5, t6, t7, t8, t9, t10, t11)
        self.perform_actions()


root = tk.Tk()
root.title("3d engine")
root.resizable(False, False)

board = Engine()
board.pack()

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
# c = (500, 200, 100)
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
