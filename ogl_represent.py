import glfw
from OpenGL.GL import *
from OpenGL.GLUT import *

from OpenGL.GL.shaders import compileProgram, compileShader
import pyrr
from Camera import Camera
import numpy as np
import h5py
import ctypes

cam1, cam2 = None, None
stereo = None

initial_width, initial_height = 2500, 1400
lastX, lastY = 0, 0
first_mouse = True
moving_camera = False
rotation = pyrr.matrix44.create_from_matrix33(pyrr.matrix33.create_identity(float))

proj_loc = None
vertices = None


# callbacks
def mouse_button_callback(window, button, action, mods):
    global moving_camera, first_mouse
    if button == glfw.MOUSE_BUTTON_RIGHT and action == glfw.PRESS:
        first_mouse = True
        moving_camera = True
    elif button == glfw.MOUSE_BUTTON_RIGHT and action == glfw.RELEASE:
        moving_camera = False


def mouse_look_callback(window, xpos, ypos):
    global lastX, lastY, first_mouse, moving_camera

    if moving_camera:
        if first_mouse:
            lastX = xpos
            lastY = ypos
            first_mouse = False

        xoffset = xpos - lastX
        # opengl coords start from bottom to top, for that reason it is inverted
        yoffset = lastY - ypos

        lastX = xpos
        lastY = ypos

        global cam1, cam2, stereo
        x_rot, y_rot = cam1.mouse_movement_rotate_item(xoffset, yoffset)
        if stereo:
            cam1.update_offset_camera(cam2)

        global rotation
        rotation = pyrr.matrix44.create_from_matrix33(pyrr.matrix33.multiply(x_rot, y_rot))

        # print(rotation)
    else:
        pass


def window_resize(window, width, height):
    global proj_loc
    glViewport(0, 0, width, height)
    projection = pyrr.matrix44.create_perspective_projection_matrix(45, width / height, 0.1, 200)
    glUniformMatrix4fv(proj_loc, 1, GL_FALSE, projection)


def scroll_callback(window, x_offset, y_offset):
    global cam1, stereo
    cam1.scroll(y_offset)
    if stereo:
        cam1.update_offset_camera(cam2)


vertex_src = """
# version 330 core

in vec3 a_position;

uniform mat4 model;
uniform mat4 projection;
uniform mat4 view;

void main()
{
    gl_Position = projection * view * model * vec4(a_position, 1.0);
}
"""

fragment_src = """
# version 330 core

out vec4 out_color;

void main()
{
    out_color = vec4(1.0, 0.0, 0.0, 1.0);
}
"""


def start_visualization(read_path, mode_stereo):
    print(read_path)

    global cam1, cam2, stereo
    stereo = mode_stereo
    if stereo:
        cam1 = Camera(0.2)
        cam2 = Camera(-0.2)
        cam_2_turn = False
    else:
        cam1 = Camera()

    # initialize library and create + verify root
    if True:
        # initializing glfw library
        if not glfw.init():
            raise Exception("glfw can not be initialized!")

        # creating the root
        ogl = glfw.create_window(initial_width, initial_height, "My OpenGL window", None, None)

        # check if root was created
        if not ogl:
            glfw.terminate()
            raise Exception("glfw root can not be created!")

    # Set callbacks and root pos
    if True:
        glfw.set_window_pos(ogl, 400, 200)

        # set the callback function for root resize
        glfw.set_window_size_callback(ogl, window_resize)

        # camera control callbacks
        glfw.set_cursor_pos_callback(ogl, mouse_look_callback)
        # glfw.set_cursor_enter_callback(root, mouse_enter_callback)
        glfw.set_mouse_button_callback(ogl, mouse_button_callback)
        # scroll wheel callback
        glfw.set_scroll_callback(ogl, scroll_callback)

    # make the context current
    glfw.make_context_current(ogl)

    # reading the file
    f = h5py.File(read_path, 'r')

    # set global variable to the pixel data
    global vertices
    vertices = f.get('xyz_data')[...]

    print(len(vertices))

    f.close()

    print(len(vertices))

    # colors is unused for now
    colors = []

    vertices = np.array(vertices, dtype=np.float32)
    colors = np.array(colors, dtype=np.float32)

    shader = compileProgram(compileShader(vertex_src, GL_VERTEX_SHADER),
                            compileShader(fragment_src, GL_FRAGMENT_SHADER))

    # create buffer and connect to where gl stores vertex data
    # vertices.nbyes = size in bytes of vertices, each is 32 bits so 4 bytes each
    VBO = glGenBuffers(1)
    glBindBuffer(GL_ARRAY_BUFFER, VBO)
    glBufferData(GL_ARRAY_BUFFER, vertices.nbytes, vertices, GL_STATIC_DRAW)

    # store the position of "a_position" attribute from shader in variable
    position = glGetAttribLocation(shader, "a_position")
    glEnableVertexAttribArray(position)
    glVertexAttribPointer(position, 3, GL_FLOAT, GL_FALSE, 0, ctypes.c_void_p(0))

    glUseProgram(shader)
    glClearColor(0.91, 0.84, 0.74, 1)

    glEnable(GL_DEPTH_TEST)
    glEnable(GL_BLEND)
    glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)

    projection = pyrr.matrix44.create_perspective_projection_matrix(45, initial_width / initial_height, 0.1, 100)
    translation = pyrr.matrix44.create_from_translation(pyrr.Vector3([0, 0, 0]))

    # eye, target, up
    # view = pyrr.matrix44.create_look_at(pyrr.Vector3([0, 0, 20]), pyrr.Vector3([0, 0, 0]), pyrr.Vector3([0, 1, 0]))
    global proj_loc
    model_loc = glGetUniformLocation(shader, "model")
    proj_loc = glGetUniformLocation(shader, "projection")
    view_loc = glGetUniformLocation(shader, "view")

    glUniformMatrix4fv(proj_loc, 1, GL_FALSE, projection)
    # glUniformMatrix4fv(view_loc, 1, GL_FALSE, view)
    model = translation

    glPointSize(1)
    # the main application loop
    while not glfw.window_should_close(ogl):
        glfw.poll_events()

        glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)

        if stereo:
            if cam_2_turn:
                view = cam2.get_view_matrix()
            else:
                view = cam1.get_view_matrix()
            cam_2_turn = not cam_2_turn
        else:
            view = cam1.get_view_matrix()

        glUniformMatrix4fv(view_loc, 1, GL_FALSE, view)

        glUniformMatrix4fv(model_loc, 1, GL_FALSE, pyrr.matrix44.multiply(translation, rotation))

        glDrawArrays(GL_POINTS, 0, int(len(vertices) / 3))

        glfw.swap_buffers(ogl)

    # terminate glfw, free up allocated resources
    glfw.terminate()
