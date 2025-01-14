import matplotlib.pyplot as plt
import matplotlib.patches as mpatches

from qkit.analysis.semiconductor.main.pre_formatted_figures import SemiFigure


class PlotterBiascoolingAccumulation(SemiFigure):
    """Plots Accumulation voltages over bias cooling voltage.
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def plot(self, data, savename="accumulations_biascooling", shape="^", size=100, transparency=1):
        self.ax.set_title("Accumulation Voltages depending on Bias Cooling")
        self.ax.set_xlabel("Bias Cooling Voltage (V)")
        self.ax.set_ylabel("Accumulation Voltage (V)")
        for cooldown in data:
            if cooldown["RT_cooldown"] == "y":
                self.ax.scatter(cooldown["bias_V"], cooldown["first_acc_V"], marker=shape, s=size, alpha=transparency, color="r")
            elif cooldown["RT_cooldown"] == "n":
                self.ax.scatter(cooldown["bias_V"], cooldown["first_acc_V"], marker=shape, s=size, alpha=transparency, color="b")
            else:
                self.ax.scatter(cooldown["bias_V"], cooldown["first_acc_V"], marker=shape, s=size, alpha=transparency, color="c")
        plt.grid()
        red_patch = mpatches.Patch(color='red', label='Cooldown from room temperature')
        blue_patch = mpatches.Patch(color='blue', label='Fast thermal cycle to 197 Kelvin')
        plt.legend(handles=[ red_patch, blue_patch])
        plt.savefig(f"{savename}.png", dpi=self.set_dpi, bbox_inches=self.set_bbox_inches)
        plt.show() 
        self.close_delete()


class PlotterBiascoolingMinimalTopgate(SemiFigure):
    """Plots the minimal topgate voltages over bias cooling voltage.
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def plot(self, data, savename="min_TG_biascooling", shape="^", size=100, transparency=1, RT="both"):
        self.ax.set_title("Minimal SET Topgate Voltages depending on Bias Cooling")
        self.ax.set_xlabel("Bias Cooling Voltage (V)")
        self.ax.set_ylabel("TG (V)")
        for cooldown in data:
            if RT == "yes":
                if cooldown["RT_cooldown"] == "y":
                    self.ax.scatter(cooldown["bias_V"], cooldown["SET_left_TG"], marker=shape, s=size, alpha=transparency, color="r")
                    self.ax.scatter(cooldown["bias_V"], cooldown["SET_right_TG"], marker=shape, s=size, alpha=transparency, color="b")
            else:
                self.ax.scatter(cooldown["bias_V"], cooldown["SET_left_TG"], marker=shape, s=size, alpha=transparency, color="r")
                self.ax.scatter(cooldown["bias_V"], cooldown["SET_right_TG"], marker=shape, s=size, alpha=transparency, color="b")
            
        plt.grid()
        red_patch = mpatches.Patch(color='red', label='left SET')
        blue_patch = mpatches.Patch(color='blue', label='right SET')
        plt.legend(handles=[ red_patch, blue_patch])
        plt.savefig(f"{savename}.png", dpi=self.set_dpi, bbox_inches=self.set_bbox_inches)
        plt.show() 
        self.close_delete()


class PlotterBiascoolingDifferenceTopgateGates(SemiFigure):
    """Plots difference of topgate and the middle gates over bias cooling voltage.
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def plot(self, data, savename="Dif_TG_middle_gates_biascooling", shape="^", size=100, transparency=1, RT="both"):
        self.ax.set_title("Difference between TG and middle gates depending on Bias Cooling")
        self.ax.set_xlabel("Bias Cooling Voltage (V)")
        self.ax.set_ylabel("TG - middle gates (V)")
        for cooldown in data:
            if RT == "yes":
                if cooldown["RT_cooldown"] == "y":
                    self.ax.scatter(cooldown["bias_V"], cooldown["SET_left_TG"] - cooldown["SET_other_gates"], marker=shape, s=size, alpha=transparency, color="r")
                    self.ax.scatter(cooldown["bias_V"], cooldown["SET_right_TG"] - cooldown["SET_other_gates"], marker=shape, s=size, alpha=transparency, color="b")
            else:
                self.ax.scatter(cooldown["bias_V"], cooldown["SET_left_TG"] - cooldown["SET_other_gates"], marker=shape, s=size, alpha=transparency, color="r")
                self.ax.scatter(cooldown["bias_V"], cooldown["SET_right_TG"] - cooldown["SET_other_gates"], marker=shape, s=size, alpha=transparency, color="b")
        
        plt.grid()
        red_patch = mpatches.Patch(color='red', label='left SET')
        blue_patch = mpatches.Patch(color='blue', label='right SET')
        plt.legend(handles=[ red_patch, blue_patch])
        plt.savefig(f"{savename}.png", dpi=self.set_dpi, bbox_inches=self.set_bbox_inches)
        plt.show() 
        self.close_delete()


class PlotterBiascoolingDifferenceTopgateBarriers(SemiFigure):
    """Plots difference of topgate and the mean of barrier gates over bias cooling voltage.
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def plot(self, data, savename="Dif_TG_barrier_gates_biascooling", shape="^", size=100, transparency=1, RT="both"):
        self.ax.set_title("Difference between TG and the mean of barrier gates depending on Bias Cooling")
        self.ax.set_xlabel("Bias Cooling Voltage (V)")
        self.ax.set_ylabel("TG - barrier gates (V)")
        for cooldown in data:
            if RT == "yes":
                if cooldown["RT_cooldown"] == "y":
                    self.ax.scatter(cooldown["bias_V"], cooldown["SET_left_TG"] - 0.5*(cooldown["SET_left_G5"] + cooldown["SET_left_G7"]), marker=shape, s=size, alpha=transparency, color="r")
                    self.ax.scatter(cooldown["bias_V"], cooldown["SET_right_TG"] - 0.5*(cooldown["SET_right_G15"] + cooldown["SET_right_G17"]), marker=shape, s=size, alpha=transparency, color="b")
            else:
                self.ax.scatter(cooldown["bias_V"], cooldown["SET_left_TG"] - 0.5*(cooldown["SET_left_G5"] + cooldown["SET_left_G7"]), marker=shape, s=size, alpha=transparency, color="r")
                self.ax.scatter(cooldown["bias_V"], cooldown["SET_right_TG"] - 0.5*(cooldown["SET_right_G15"] + cooldown["SET_right_G17"]), marker=shape, s=size, alpha=transparency, color="b")
        
        plt.grid()
        red_patch = mpatches.Patch(color='red', label='left SET')
        blue_patch = mpatches.Patch(color='blue', label='right SET')
        plt.legend(handles=[ red_patch, blue_patch])
        plt.savefig(f"{savename}.png", dpi=self.set_dpi, bbox_inches=self.set_bbox_inches)
        plt.show() 
        self.close_delete()


class PlotterBiascoolingDifferenceBarrierGates(SemiFigure):
    """Plots difference of both barrier gates over bias cooling voltage.
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def plot(self, data, savename="Dif_barrier_gates_biascooling", shape="^", size=100, transparency=1, RT="both"):
        self.ax.set_title("Difference between both Barrier Gates depending on Bias Cooling")
        self.ax.set_xlabel("Bias Cooling Voltage (V)")
        self.ax.set_ylabel("Difference Barriers (V)")
        for cooldown in data:
            if RT == "yes":
                if cooldown["RT_cooldown"] == "y":
                    self.ax.scatter(cooldown["bias_V"], cooldown["SET_left_G5"] - cooldown["SET_left_G7"], marker=shape, s=size, alpha=transparency, color="r")
                    self.ax.scatter(cooldown["bias_V"], cooldown["SET_right_G15"] - cooldown["SET_right_G17"], marker=shape, s=size, alpha=transparency, color="b")
            else:
                self.ax.scatter(cooldown["bias_V"], cooldown["SET_left_G5"] - cooldown["SET_left_G7"], marker=shape, s=size, alpha=transparency, color="r")
                self.ax.scatter(cooldown["bias_V"], cooldown["SET_right_G15"] - cooldown["SET_right_G17"], marker=shape, s=size, alpha=transparency, color="b")
        
        plt.grid()
        red_patch = mpatches.Patch(color='red', label='left SET')
        blue_patch = mpatches.Patch(color='blue', label='right SET')
        plt.legend(handles=[ red_patch, blue_patch])
        plt.savefig(f"{savename}.png", dpi=self.set_dpi, bbox_inches=self.set_bbox_inches)
        plt.show() 
        self.close_delete()


class PlotterBiascoolingDifferenceTopgateAccumulation(SemiFigure):
    """Plots difference of topgate and first accumulation voltage over bias cooling voltage.
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def plot(self, data, savename="Dif_TG_accumulation_biascooling", shape="^", size=100, transparency=1, RT="both"):
        self.ax.set_title("Difference between TG and Accumulation Voltage depending on Bias Cooling")
        self.ax.set_xlabel("Bias Cooling Voltage (V)")
        self.ax.set_ylabel("TG - firs accumulation (V)")
        for cooldown in data:
            if RT == "yes":
                if cooldown["RT_cooldown"] == "y":
                    self.ax.scatter(cooldown["bias_V"], cooldown["SET_left_TG"] - cooldown["first_acc_V"], marker=shape, s=size, alpha=transparency, color="r")
                    self.ax.scatter(cooldown["bias_V"], cooldown["SET_right_TG"] - cooldown["first_acc_V"], marker=shape, s=size, alpha=transparency, color="b")
            else:
                self.ax.scatter(cooldown["bias_V"], cooldown["SET_left_TG"] - cooldown["first_acc_V"], marker=shape, s=size, alpha=transparency, color="r")
                self.ax.scatter(cooldown["bias_V"], cooldown["SET_right_TG"] - cooldown["first_acc_V"], marker=shape, s=size, alpha=transparency, color="b")
        
        plt.grid()
        red_patch = mpatches.Patch(color='red', label='left SET')
        blue_patch = mpatches.Patch(color='blue', label='right SET')
        plt.legend(handles=[ red_patch, blue_patch])
        plt.savefig(f"{savename}.png", dpi=self.set_dpi, bbox_inches=self.set_bbox_inches)
        plt.show() 
        self.close_delete()
