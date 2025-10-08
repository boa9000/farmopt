import allocator
import modeling as mdl
import data_retriever as dr
import ipywidgets as widgets
from IPython.display import display, clear_output



# wr = dr.WeatherRetriever()

# wr.get_coordinates()

# wr.set_constraints()

# md = mdl.ModelData(wr)
# fm = mdl.FarmModel(md)
# alc = allocator.Allocator(wr, fm)

# alc.mapper()

# alc.run()



# class MapInterface:
#     def __init__(self):
#         self.wr = dr.WeatherRetriever()
#         self.state = 0

#         self.btn_start = widgets.Button(description="Start", button_style="success")
#         self.btn_back = widgets.Button(description="Back", button_style="info")
#         self.btn_next = widgets.Button(description="Next", button_style="primary")

#         self.btn_start.disabled = True
#         self.btn_back.disabled = True
#         self.btn_next.disabled = True

#         self.btn_next.on_click(self.next_clicked)
#         self.btn_back.on_click(self.back_clicked)
        
#         # self.wr.get_coordinates()
#         # self.wr.set_constraints()
#         # self.md = mdl.ModelData(self.wr)
#         # self.fm = mdl.FarmModel(self.md)
#         # self.alc = allocator.Allocator(self.wr, self.fm)
#         # self.m = None

#     def start(self):
#         self.m = self.wr.get_coordinates()
#         self.btn_next.disabled = False
#         display(widgets.HBox([self.btn_back, self.btn_start, self.btn_next]))
#         display(self.m)
        

#     def next_clicked(self, b):
#         self.state += 1
#         self.update()
    

#     def back_clicked(self, b):
#         self.state -= 1
#         self.update()

#     def start_clicked(self, b):
#         self.alc.run()
#         self.btn_start.disabled = True
    
#     def update(self):
#         if self.state == 0:
#             clear_output()
#             self.m = self.wr.get_coordinates()
#             self.btn_next.disabled = False
#             self.btn_back.disabled = True
#             self.btn_start.disabled = True
#             display(widgets.HBox([self.btn_back, self.btn_start, self.btn_next]))
#             display(self.m)
#         elif self.state == 1:
#             clear_output()
#             self.m = self.wr.set_constraints()
#             self.btn_next.disabled = False
#             self.btn_back.disabled = False
#             self.btn_start.disabled = True
#             display(widgets.HBox([self.btn_back, self.btn_start, self.btn_next]))
#             display(self.m)
#         elif self.state == 2:
#             clear_output()
#             self.md = mdl.ModelData(self.wr)
#             self.fm = mdl.FarmModel(self.md)
#             self.alc = allocator.Allocator(self.wr, self.fm)
#             self.m = self.alc.mapper()
#             self.btn_next.disabled = True
#             self.btn_back.disabled = False
#             self.btn_start.disabled = False
#             display(widgets.HBox([self.btn_back, self.btn_start, self.btn_next]))
#             display(self.m)


#     def clear_map(self):
#         self.m.clear_controls()

#     def run_allocation(self):
#         if self.m is None:
#             raise ValueError("Map not initialized. Please call show_map() first.")
#         self.alc.run()
#         return self.alc


import ipywidgets as widgets
from IPython.display import display, clear_output

class MapInterface:
    def __init__(self):
        self.wr = dr.WeatherRetriever()
        self.state = 0


        self.step_label = widgets.Label(value="Step 1/3: Draw farm area")

        self.iterations = 20
        self.iter_slider = widgets.IntSlider(value=self.iterations, min=1, max=100, description="Iterations")
        self.turbines_no_slider = widgets.IntSlider(value=5, min=2, max=15, description="Turbines")
        self.no_of_turbines = self.turbines_no_slider.value

        self.btn_start = widgets.Button(description="Start", button_style="success")
        self.btn_back = widgets.Button(description="Back", button_style="info")
        self.btn_next = widgets.Button(description="Next", button_style="primary")

        self.btn_start.disabled = True
        self.btn_back.disabled = True
        self.btn_next.disabled = True

        self.btn_next.on_click(self.next_clicked)
        self.btn_back.on_click(self.back_clicked)
        self.btn_start.on_click(self.start_clicked)

        self.output = widgets.Output()

       
        self.buttons_box = widgets.HBox([self.btn_back, self.btn_start, self.btn_next])
        self.ui_box = widgets.VBox([self.step_label, self.iter_slider, self.turbines_no_slider, self.buttons_box])
        display(self.ui_box, self.output)
        self.start()


    def start(self):
        self.state = 0
        self.update()

    def next_clicked(self, b):
        self.state = min(self.state + 1, 2)
        self.update()

    def back_clicked(self, b):
        self.state = max(self.state - 1, 0)
        self.update()

    def start_clicked(self, b):
        self.iterations = self.iter_slider.value
        self.alc.update_iterations(self.iterations)
        self.alc.run()
        self.btn_start.disabled = True


    def update(self):
        # Update step label
        if self.state == 0:
            self.step_label.value = "Step 1/3: Draw farm area"
            self.btn_back.disabled = True
            self.btn_next.disabled = False
            self.btn_start.disabled = True
            self.turbines_no_slider.disabled = False
            self.iter_slider.disabled = False
        elif self.state == 1:
            self.step_label.value = "Step 2/3: Set constraints"
            self.btn_back.disabled = False
            self.btn_next.disabled = False
            self.btn_start.disabled = True
            self.turbines_no_slider.disabled = False
            self.iter_slider.disabled = False
        elif self.state == 2:
            self.no_of_turbines = self.turbines_no_slider.value
            self.step_label.value = "Step 3/3: Run optimization by clicking Start"
            self.btn_back.disabled = False
            self.btn_next.disabled = True
            self.btn_start.disabled = False
            self.turbines_no_slider.disabled = True
            self.iter_slider.disabled = True


        with self.output:
            clear_output()
            if self.state == 0:
                self.m = self.wr.get_coordinates()
            elif self.state == 1:
                self.m = self.wr.set_constraints()
            elif self.state == 2:
                self.md = mdl.ModelData(self.wr)
                self.fm = mdl.FarmModel(self.md, no_of_turbines=self.no_of_turbines)
                self.alc = allocator.Allocator(self.wr, self.fm)
                self.m = self.alc.mapper()
            display(self.m)
