import tkinter as tk
import time
import threading
import random
import math

class Node(object):
    def __init__(self, canvas, width, cor_x, cor_y):
        self.canvas = canvas
        self.width = width
        self.cor_x = cor_x
        self.cor_y = cor_y

        self.outgoing_edges = []
        self.incoming_edges = []

        self.height = 0

        self.entity = self.canvas.create_oval(cor_x-self.width/2,cor_y-self.width/2,cor_x+self.width/2,cor_y+self.width/2, fill="blue")

        self.last_flipped_edges = []

    def get_distance(self, posxy):
        x,y = posxy
        return math.hypot(self.cor_x-x,self.cor_y-y)

class Arrow(object):
    def __init__(self, canvas, arrow_tip_length, n1, n2):
        self.canvas = canvas
        self.arrow_tip_length = arrow_tip_length
        self.arrow_tip_width = 0.8 * self.arrow_tip_length

        self.nodes = [n1,n2]
        self.start_node = 0 # n1:0, n2:1 initially n1 is start node
        self.end_node = 1

        self.create_arrow()

    def create_arrow(self):
        x1 = self.nodes[self.start_node].cor_x
        y1 = self.nodes[self.start_node].cor_y
        x2 = self.nodes[self.end_node].cor_x
        y2 = self.nodes[self.end_node].cor_y

        node_distance = math.hypot(x1-x2,y1-y2)

        begin_ratio = ((self.nodes[self.end_node].width/2)+1)/node_distance
        end_ratio = 1-((self.nodes[self.start_node].width/2)+1)/node_distance

        x1 = begin_ratio*x2+(1-begin_ratio)*x1
        y1 = begin_ratio*y2+(1-begin_ratio)*y1
        x2 = end_ratio*x2+(1-end_ratio)*x1
        y2 = end_ratio*y2+(1-end_ratio)*y1

        arrow_direction = math.atan2(y2-y1,x2-x1)

        p1_ratio = self.arrow_tip_length/node_distance

        p1x = p1_ratio*x1+(1-p1_ratio)*x2
        p1y = p1_ratio*y1+(1-p1_ratio)*y2

        left_wing_direction = arrow_direction+math.pi/2
        right_wing_direction = arrow_direction-math.pi/2

        left_wing_offset_x = math.cos(left_wing_direction)*self.arrow_tip_width/2
        left_wing_offset_y = math.sin(left_wing_direction)*self.arrow_tip_width/2
        right_wing_offset_x = math.cos(right_wing_direction)*self.arrow_tip_width/2
        right_wing_offset_y = math.sin(right_wing_direction)*self.arrow_tip_width/2

        p2x = p1x+left_wing_offset_x
        p2y = p1y+left_wing_offset_y
        p3x = p1x+right_wing_offset_x
        p3y = p1y+right_wing_offset_y

        self.entity = self.canvas.create_line(x1,y1, p1x,p1y, p2x,p2y, x2,y2, p3x,p3y, p1x,p1y, width=2)

        self.nodes[self.start_node].outgoing_edges.append(self)
        self.nodes[self.end_node].incoming_edges.append(self)

    def flip(self):
        self.nodes[self.start_node].outgoing_edges.remove(self)
        self.nodes[self.end_node].incoming_edges.remove(self)
#        print("flipping: {},{}".format(self.nodes[self.start_node].entity,self.nodes[self.end_node].entity), end=" -> ")

        self.start_node += 1
        self.end_node += 1
        self.start_node %= 2
        self.end_node %= 2

        self.canvas.delete(self.entity)
        self.create_arrow()
#        print("{},{}".format(self.nodes[self.start_node].entity,self.nodes[self.end_node].entity))


class SimulationCanvas(threading.Thread):
    def __init__(self, simulation, width, height):
        super().__init__()
        self.simulation = simulation
        self.width = width
        self.height = height
        self.canvas = tk.Canvas(self.simulation.root, width=self.width, height=self.height, borderwidth=0, highlightthickness=0, bg="#DDD")
        self.canvas.grid(row=0, column=1, padx=10, pady=10)

        self.node_width = 30
        self.node_min_distance = 60
        self.node_at_most_one_max_distance = 100
        self.update_rate = 10 #fps

        self.canvas.bind("<Button-1>", self.mouse_click_callback_left)
        self.canvas.bind("<Button-3>", self.mouse_click_callback_right)

        self.edge_flip_iteration_state = 0
        self.edges_to_flip = []

        self.algorithm = "full"
        self.edges_last_flipped = []
        self.nodes_to_clear = [] # clear last flipped edges-lists

    def create_random_nodes(self, number_nodes):
        self.nodes = []

        while len(self.nodes) < number_nodes:
            self.canvas.update()
            cor_x = random.randint(self.node_width/2,self.width-self.node_width/2)
            cor_y = random.randint(self.node_width/2,self.height-self.node_width/2)
            dists = [n.get_distance((cor_x,cor_y)) for n in self.nodes]
            if all(dist > self.node_min_distance for dist in dists) and any(dist < self.node_at_most_one_max_distance for dist in dists):
                new_node = Node(self.canvas, self.node_width, cor_x, cor_y)
                self.nodes.append(new_node)
            elif len(self.nodes) == 0:
                new_node = Node(self.canvas, self.node_width, cor_x, cor_y)
                self.nodes.append(new_node)
                self.rooted_node = self.nodes[0]
                self.canvas.itemconfigure(self.rooted_node.entity, fill="green")

    def connect_nodes(self):
        self.edges = []
        for n1_i,n1 in enumerate(self.nodes):
            for n2_i in range(n1_i+1,len(self.nodes)):
                self.canvas.update()
                n2 = self.nodes[n2_i]

                dist = n1.get_distance((n2.cor_x,n2.cor_y))
                if dist < self.node_at_most_one_max_distance:
                    new_arrow = Arrow(self.canvas, 20, n1, n2)
                    self.edges.append(new_arrow)

    def mouse_click_callback_right(self, event):
        for n in self.nodes:
            clickdist = n.get_distance((event.x,event.y))
            if clickdist < self.node_width/2:
                self.edge_flip_iteration_state = 0
#                self.edges_flip_cache = []
                for edge in self.edges:
                    self.canvas.itemconfigure(edge.entity, fill="black")
                self.canvas.itemconfigure(self.rooted_node.entity, fill="blue")
                self.rooted_node = n
                self.canvas.itemconfigure(self.rooted_node.entity, fill="green")

    def mouse_click_callback_left(self, event):
        to_remove = []
        for n in self.nodes:
            clickdist = n.get_distance((event.x,event.y))
            if clickdist <= n.width/2:
                self.edge_flip_iteration_state = 0
#                self.edges_flip_cache = []
                for edge in n.outgoing_edges:
                    self.canvas.delete(edge.entity)
                    edge.nodes[edge.end_node].incoming_edges.remove(edge)
                    self.edges.remove(edge)
                for edge in n.incoming_edges:
                    self.canvas.delete(edge.entity)
                    edge.nodes[edge.start_node].outgoing_edges.remove(edge)
                    self.edges.remove(edge)
                to_remove.append(n)
        for n in to_remove:
            self.canvas.delete(n.entity)
            self.nodes.remove(n)

    def convert_to_dag(self):
        nodes_to_do = [self.rooted_node]
        nodes_done = []

        height = 0
        while len(nodes_to_do) > 0:
            n = nodes_to_do.pop(0)
            if n not in nodes_done:
                n.height = height
                height += 1
                nodes_done.append(n)
                for edge in n.outgoing_edges:
                    nodes_to_do.append(edge.nodes[edge.end_node])
                for edge in n.incoming_edges:
                    nodes_to_do.append(edge.nodes[edge.start_node])

        for edge in self.edges:
            if edge.nodes[edge.start_node].height < edge.nodes[edge.end_node].height:
                edge.flip()

    def edge_flip_iteration(self):
        if self.edge_flip_iteration_state == 0:
            self.edges_to_flip = []
            for node in self.nodes:
                number_outgoing_edges = len(node.outgoing_edges)
                if number_outgoing_edges == 0 and not node == self.rooted_node:
                    if all(edge in node.last_flipped_edges for edge in node.incoming_edges):
                        for edge in node.incoming_edges:
                            self.canvas.itemconfigure(edge.entity, fill="yellow")
                            self.edges_to_flip.append(edge)
                        self.canvas.itemconfig(node.entity, fill="cyan")
                    else:
                        for edge in node.incoming_edges:
                            if not edge in node.last_flipped_edges:
                                self.canvas.itemconfigure(edge.entity, fill="yellow")
                                self.edges_to_flip.append(edge)

            for edge in self.rooted_node.outgoing_edges:
                self.canvas.itemconfigure(edge.entity, fill="yellow")
                self.edges_to_flip.append(edge)
            self.edges_to_flip = list(set(self.edges_to_flip))
        else:
            for edge in self.edges_to_flip:
                edge.flip()
                self.canvas.itemconfigure(edge.entity, fill="red")
                if self.algorithm == "partial":
                    edge.nodes[edge.end_node].last_flipped_edges.append(edge)
                    edge.nodes[edge.start_node].last_flipped_edges = []

        # change edge_flip_state
        self.edge_flip_iteration_state += 1
        self.edge_flip_iteration_state %= 2

#    def edge_flip_iteration_undo(self):
#        if self.edge_flip_iteration_state == 0:
#            if len(self.edges_flip_cache) > 0:
#                edges,edges_last_flipped = self.edges_flip_cache.pop(-1)
#                for edge in edges:
#                    edge.flip()
#                    self.canvas.itemconfigure(edge.entity, fill="green")
#            self.edge_flip_iteration_state = 1

    def run(self):
        while True:
            loop_start_time = time.time()

            self.canvas.update()

            loop_end_time = time.time()
            sleep_time = max(0, (1/self.update_rate)-(loop_end_time-loop_start_time))

            time.sleep(sleep_time)



class Simulation(object):
    def __init__(self,width,height):
        self.width = width
        self.height = height

        self.root = tk.Tk()
        self.root.config(background = "white")

        self.left_frame = tk.Frame(self.root,width=200,height=self.height, bg="#F5F5F5")
        self.left_frame.grid(row=0,column=0,padx=10,pady=10)

        self.slider_num_nodes = tk.Scale(self.left_frame, from_=5, to=180, resolution=5, orient=tk.HORIZONTAL, length=160)
        self.slider_num_nodes.grid(row=0, column=0, padx=5, pady=5)

        self.button_start_simulation = tk.Button(self.left_frame, text="Start Simulation", bg="#00F0FF", width=20, font="Monospace", command=self.button_start_simulation_callback)
        self.button_start_simulation.grid(row=2, column=0, padx=5, pady=5)

        self.frame_algorithm_selection = tk.Frame(self.left_frame)
        self.frame_algorithm_selection.grid(row=3, column=0, padx=5, pady=5)
        self.algorithm_selection_string_var = tk.StringVar()
        self.algorithm_selection_string_var.set("full")
        self.radiobutton_algorithm_selection_1 = tk.Radiobutton(self.frame_algorithm_selection, text="full", variable=self.algorithm_selection_string_var, value="full", command=self.radiobutton_algorithm_selection_callback)
        self.radiobutton_algorithm_selection_1.grid(row=0, column=0, padx=5, pady=5)
        self.radiobutton_algorithm_selection_2 = tk.Radiobutton(self.frame_algorithm_selection, text="partial", variable=self.algorithm_selection_string_var, value="partial", command=self.radiobutton_algorithm_selection_callback)
        self.radiobutton_algorithm_selection_2.grid(row=0, column=1, padx=5, pady=5)

        self.button_edge_flip_iteration = tk.Button(self.left_frame, text="Iteration Step", bg="#00F0FF", width=20, font="Monospace", command=self.button_edge_flip_iteration_callback)
        self.button_edge_flip_iteration.grid(row=4, column=0, padx=5, pady=5)

#        self.button_edge_flip_iteration_undo = tk.Button(self.left_frame, text="Iteration Undo", bg="#00F0FF", width=20, font="Monospace", command=self.button_edge_flip_iteration_undo_callback)
#        self.button_edge_flip_iteration_undo.grid(row=5, column=0, padx=5, pady=5)

        self.simulation_canvas = SimulationCanvas(self, self.width-200,self.height)
        self.simulation_canvas.start()

        self.root.wm_title("Link Reversal Simulation")
        self.root.mainloop()

    def button_start_simulation_callback(self):
        number_nodes = self.slider_num_nodes.get()
        self.simulation_canvas.canvas.delete("all")
        self.simulation_canvas.create_random_nodes(number_nodes)
        self.simulation_canvas.connect_nodes()
        self.simulation_canvas.convert_to_dag()
        self.simulation_canvas.edge_flip_iteration_state = 0
#        self.simulation_canvas.edges_flip_cache = []

    def button_edge_flip_iteration_callback(self):
        self.simulation_canvas.edge_flip_iteration()

#    def button_edge_flip_iteration_undo_callback(self):
#        self.simulation_canvas.edge_flip_iteration_undo()

    def radiobutton_algorithm_selection_callback(self):
        self.simulation_canvas.algorithm = self.algorithm_selection_string_var.get()

if __name__ == "__main__":

    simulation = Simulation(1500,800)
