import math

def sort_triangles_by_z(t1, t2):
    z1 = (t1.vertices[0].z+t1.vertices[1].z+t1.vertices[2].z)/3.0
    z2 = (t2.vertices[0].z+t2.vertices[1].z+t2.vertices[2].z)/3.0
    return z2 - z1


class Zbuffer:
    def __init__(self, width, height):
        self.buffer = []
        self.width = width
        self.height = height
        self.clear()

    def clear(self):
        for _ in range(0, self.width*self.height):
            self.buffer.append(math.inf)

    def at(self, x, y):
        return self.buffer[y*self.width+x]

    def testAndSet(self, x, y, depth):
        d = self.at(x, y)
        if(depth < d):
            d = depth
            return True
        return False


class vec3d:
    def __init__(self, x, y, z, w=None) -> None:
        self.x = x
        self.y = y
        self.z = z
        self.w = w if w else 1.0

    def aslist(self):
        return [self.x, self.y, self.z]

    def __str__(self):
        return f"({self.x}, {self.y}, {self.z})"


class triangle:
    def __init__(self, p1, p2, p3) -> None:
        if(type(p1) == vec3d):
            self.vertices = [p1, p2, p3]
        else:
            self.vertices = [vec3d(*p1), vec3d(*p2), vec3d(*p3)]

        self.color = vec3d(255, 255, 255)


class mesh:
    ambientColor = vec3d(255, 255, 255)

    def __init__(self, *args):
        self.tris = [*args]

        # print(self.tris)

    def loadmodelfromfile(self, file):
        # load wavefront obj file
        with open(file, "r") as f:
            v = []
            tris = []
            while(True):
                l = f.readline().strip()
                if(len(l) == 0):
                    break
                if l[0] == "v":
                    # is vertex
                    data = list(map(lambda x: float(x), l[2:].split(" ")))
                    v.append(vec3d(data[0], data[1], data[2]))
                elif l[0] == "f":
                    # isface
                    data = list(map(lambda x: int(x), l[2:].split(" ")))
                    t = triangle(v[data[0]-1], v[data[1]-1], v[data[2]-1])
                    tris.append(t)
        print(
            f"Loaded model {file} with {len(tris)} faces and {len(v)} vertices.")
        self.tris = tris

    def setAmbientColor(self, color: vec3d):
        self.ambientColor = color

    # def getAmbientColor(self):
    #     return self.ambientColor


class mat4x4:
    def __init__(self):
        self.mat = [[0.0, 0.0, 0.0, 0.0], [0.0, 0.0, 0.0, 0.0],
                    [0.0, 0.0, 0.0, 0.0], [0.0, 0.0, 0.0, 0.0]]


def rgbToHex(color: vec3d) -> str:
    c = vec3d(color.x, color.y, color.z)

    c.x = min(255, max(0, c.x))
    c.y = min(255, max(0, c.y))
    c.z = min(255, max(0, c.z))

    return f"#{c.x:02x}{c.y:02x}{c.z:02x}"


def matmatmul(m1: mat4x4, m2: mat4x4) -> mat4x4:
    mout = mat4x4()
    for c in range(0, 4):
        for r in range(0, 4):
            mout.mat[r][c] = m1.mat[r][0] * m2.mat[0][c] + m1.mat[r][1] * \
                m2.mat[1][c] + m1.mat[r][2] * \
                m2.mat[2][c] + m1.mat[r][3] * m2.mat[3][c]
    return mout


def matPointAt(pos: vec3d, target: vec3d, up: vec3d) -> mat4x4:
    m = mat4x4()
    newForward = vec_normalize(vec_sub(target, pos))

    a = vec_mul(newForward, dot(up, newForward))
    newup = vec_normalize(vec_sub(up, a))

    newRight = cross(newup, newForward)

    matrix = mat4x4()
    matrix.mat[0][0] = newRight.x
    matrix.mat[1][0] = newup.x
    matrix.mat[2][0] = newForward.x
    matrix.mat[3][0] = pos.x

    matrix.mat[0][1] = newRight.y
    matrix.mat[1][1] = newup.y
    matrix.mat[2][1] = newForward.y
    matrix.mat[3][1] = pos.y

    matrix.mat[0][2] = newRight.z
    matrix.mat[1][2] = newup.z
    matrix.mat[2][2] = newForward.z
    matrix.mat[3][2] = pos.z

    matrix.mat[0][3] = 0
    matrix.mat[1][3] = 0
    matrix.mat[2][3] = 0
    matrix.mat[3][3] = 1

    return matrix


def matQuickInverse(m: mat4x4) -> mat4x4:
    matrix = mat4x4()
    matrix.mat[0][0] = m.mat[0][0]
    matrix.mat[1][0] = m.mat[0][1]
    matrix.mat[2][0] = m.mat[0][2]

    matrix.mat[0][1] = m.mat[1][0]
    matrix.mat[1][1] = m.mat[1][1]
    matrix.mat[2][1] = m.mat[1][2]

    matrix.mat[0][2] = m.mat[2][0]
    matrix.mat[1][2] = m.mat[2][1]
    matrix.mat[2][2] = m.mat[2][2]

    matrix.mat[0][3] = 0.0
    matrix.mat[1][3] = 0.0
    matrix.mat[2][3] = 0.0

    matrix.mat[3][0] = -(m.mat[3][0]*matrix.mat[0][0] + m.mat[3]
                         [1]*matrix.mat[1][0] + m.mat[3][2]*matrix.mat[2][0])
    matrix.mat[3][1] = -(m.mat[3][0]*matrix.mat[0][1] + m.mat[3]
                         [1]*matrix.mat[1][1] + m.mat[3][2]*matrix.mat[2][1])
    matrix.mat[3][2] = -(m.mat[3][0]*matrix.mat[0][2] + m.mat[3]
                         [1]*matrix.mat[1][2] + m.mat[3][2]*matrix.mat[2][2])
    matrix.mat[3][3] = 1.0

    return matrix


def mulVecMat(i: vec3d, matrix: mat4x4) -> vec3d:
    output = vec3d(0.0, 0.0, 0.0, 0.0)
    m = matrix.mat
    output.x = i.x * m[0][0] + i.y * m[1][0] + i.z * m[2][0] + i.w*m[3][0]
    output.y = i.x * m[0][1] + i.y * m[1][1] + i.z * m[2][1] + i.w*m[3][1]
    output.z = i.x * m[0][2] + i.y * m[1][2] + i.z * m[2][2] + i.w*m[3][2]
    output.w = i.x * m[0][3] + i.y * m[1][3] + i.z * m[2][3] + i.w*m[3][3]

    # if(w != 0):
    #     output.x /= w
    #     output.y /= w
    #     output.z /= w

    return output


def vecIntersectPlane(plane_point: vec3d, plane_normal: vec3d, lineStart: vec3d, lineEnd: vec3d) -> vec3d:
    # returns vector if the line crosses plane
    # plane_point is a point on the plane
    # plane normal is the plane's normal
    # together they can describe the plane
    plane_normal = vec_normalize(plane_normal)
    plane_d = -dot(plane_normal, plane_point)
    ad = dot(lineStart, plane_normal)
    bd = dot(lineEnd, plane_normal)
    t = (-plane_d-ad) / (bd-ad)
    lineStartToEnd = vec_sub(lineEnd, lineStart)
    lineToIntersect = vec_mul(lineStartToEnd, t)
    return vec_add(lineStart, lineToIntersect)


def dist(p, plane_n, plane_p):
    # returns distance between point p and the plane made by normal n and a point on the plane (plane_p)
    # n = vec_normalize(p)
    return (plane_n.x*p.x+plane_n.y*p.y+plane_n.z*p.z - dot(plane_n, plane_p))


def triangleClipAgainstPlane(plane_point: vec3d, plane_normal: vec3d, triangle_in: triangle) -> tuple:
    plane_normal = vec_normalize(plane_normal)

    inside_points = [0.0]*3
    outside_points = [0.0]*3
    nInsidePointCount = 0
    nOutsidePointCount = 0

    d0 = dist(triangle_in.vertices[0], plane_normal, plane_point)
    d1 = dist(triangle_in.vertices[1], plane_normal, plane_point)
    d2 = dist(triangle_in.vertices[2], plane_normal, plane_point)

    if(d0 >= 0):
        inside_points[nInsidePointCount] = triangle_in.vertices[0]
        nInsidePointCount += 1
    else:
        outside_points[nOutsidePointCount] = triangle_in.vertices[0]
        nOutsidePointCount += 1

    if(d1 >= 0):
        inside_points[nInsidePointCount] = triangle_in.vertices[1]
        nInsidePointCount += 1
    else:
        outside_points[nOutsidePointCount] = triangle_in.vertices[1]
        nOutsidePointCount += 1
    if(d2 >= 0):
        inside_points[nInsidePointCount] = triangle_in.vertices[2]
        nInsidePointCount += 1
    else:
        outside_points[nOutsidePointCount] = triangle_in.vertices[2]
        nOutsidePointCount += 1

    if(nInsidePointCount == 0):
        return (0, 0)
    if(nInsidePointCount == 3):
        # triangle_in.color = vec3d(255, 255, 255)
        return (1, triangle_in)

    if(nInsidePointCount == 1 and nOutsidePointCount == 2):
        # clip to new triangle
        v0 = inside_points[0]

        v1 = vecIntersectPlane(plane_point, plane_normal,
                               inside_points[0], outside_points[0])
        v2 = vecIntersectPlane(plane_point, plane_normal,
                               inside_points[0], outside_points[1])
        tout1 = triangle(v0, v1, v2)

        tout1.color = vec_add(triangle_in.color, vec3d(0, 0, 0))

        return (1, tout1)

    if(nInsidePointCount == 2 and nOutsidePointCount == 1):
        # clip to quad (2 new triangles)
        v0 = inside_points[0]
        v1 = inside_points[1]
        v2 = vecIntersectPlane(plane_point, plane_normal,
                               inside_points[0], outside_points[0])

        v3 = inside_points[1]
        v4 = v2
        v5 = vecIntersectPlane(plane_point, plane_normal,
                               inside_points[1], outside_points[0])

        tout1 = triangle(v0, v1, v2)
        tout2 = triangle(v3, v4, v5)
        tout1.color = vec_add(triangle_in.color, vec3d(0, 0, 0))
        tout2.color = vec_add(triangle_in.color, vec3d(0, 0, 0))

        return (2, tout1, tout2)


def makeMatRotationY(angleRad: float) -> mat4x4:
    m = mat4x4()
    m.mat[0][0] = math.cos(angleRad)
    m.mat[0][2] = math.sin(angleRad)
    m.mat[2][0] = -math.sin(angleRad)
    m.mat[1][1] = 1.0
    m.mat[2][2] = math.cos(angleRad)
    m.mat[3][3] = 1.0
    return m


def makeMatRotationZ(angleRad: float) -> mat4x4:
    m = mat4x4()
    m.mat[0][0] = math.cos(angleRad)
    m.mat[0][1] = math.sin(angleRad)
    m.mat[1][0] = -math.sin(angleRad)
    m.mat[1][1] = math.cos(angleRad)
    m.mat[2][2] = 1.0
    m.mat[3][3] = 1.0
    return m


def makeMatRotationX(angleRad: float) -> mat4x4:
    m = mat4x4()
    m.mat[0][0] = 1.0
    m.mat[1][1] = math.cos(angleRad)
    m.mat[1][2] = math.sin(angleRad)
    m.mat[2][1] = -math.sin(angleRad)
    m.mat[2][2] = math.cos(angleRad)
    m.mat[3][3] = 1.0
    return m


def makeMatTranslation(x, y, z) -> mat4x4:
    m = mat4x4()
    m.mat[0][0] = 1.0
    m.mat[1][1] = 1.0
    m.mat[2][2] = 1.0
    m.mat[3][3] = 1.0
    m.mat[3][0] = x
    m.mat[3][1] = y
    m.mat[3][2] = z
    return m


def makeMatProjection(fFov, aspectratio, fNear, fFar) -> mat4x4:
    # convert to degrees
    fFovRad = 1.0/math.tan(fFov*0.5/180.0*3.14159)

    m = mat4x4()
    m.mat[0][0] = aspectratio*fFovRad
    m.mat[1][1] = fFovRad
    m.mat[2][2] = fFar/(fFar-fNear)
    m.mat[3][2] = (-fFar*fNear)/(fFar-fNear)
    m.mat[2][3] = 1.0
    m.mat[3][3] = 0.0
    return m


def vec_add(v1: vec3d, v2: vec3d) -> vec3d:
    return vec3d(v1.x+v2.x, v1.y+v2.y, v1.z+v2.z)


def vec_sub(v1: vec3d, v2: vec3d) -> vec3d:
    return vec3d(v1.x-v2.x, v1.y-v2.y, v1.z-v2.z)


def vec_mul(v1: vec3d, k: float) -> vec3d:
    return vec3d(v1.x*k, v1.y*k, v1.z*k)


def vec_div(v1: vec3d, k: float) -> vec3d:
    return vec3d(v1.x/k, v1.y/k, v1.z/k)


def dot(v1: vec3d, v2: vec3d) -> float:
    return v1.x*v2.x+v1.y*v2.y+v1.z*v2.z


def cross(v1: vec3d, v2: vec3d) -> vec3d:
    return vec3d(v1.y*v2.z-v1.z*v2.y,
                 v1.z*v2.x-v1.x*v2.z,
                 v1.x*v2.y-v1.y*v2.x)


def vec_len(v: vec3d) -> vec3d:
    return math.sqrt(dot(v, v))


def vec_normalize(v: vec3d) -> vec3d:
    l = vec_len(v)
    return vec3d(v.x/l, v.y/l, v.z/l)


def makeMatIdentity() -> mat4x4:
    m = mat4x4()
    m.mat[0][0] = 1.0
    m.mat[1][1] = 1.0
    m.mat[2][2] = 1.0
    m.mat[3][3] = 1.0
    return m
