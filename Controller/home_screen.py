"""_module summary_"""

import importlib
from decimal import Decimal

import View.HomeScreen.home_screen
from Utils import helpers
from View import HomeScreenView

# We have to manually reload the view module in order to apply the
# changes made to the code on a subsequent hot reload.
# If you no longer need a hot reload, you can delete this instruction.
importlib.reload(View.HomeScreen.home_screen)


class HomeScreenController:
    """
    The `HomeScreenController` class represents a controller implementation.
    Coordinates work of the view with the model.
    The controller implements the strategy pattern. The controller connects to
    the view to control its actions.
    """

    def __init__(self, model):
        self.model = model  # Model.home_screen.HomeScreenModel
        self.views = [HomeScreenView(controller=self, model=self.model)]
        self.no_of_parts = 4
        self.done_progress = 0.0

    def get_views(self) -> list[HomeScreenView]:
        """Gets the view connected to this controller.

        Returns:
            list[HomeScreenView]: The views connected to this controller.
        """
        return self.views

    def change_screen(self, direction: str, next_screen: str):
        """Go to the next screen.

        Args:
            direction (str): the transition direction
            next_screen (str): the next screen to go to.
        """
        self.views[0].change_screen(direction, next_screen)

    def load_user_data(self, do_reload=False):
        """Loads all user information."""
        self.done_progress = 0.0 if do_reload else self.done_progress
        if self.done_progress <= 0:
            self.views[0].loading_view.open()
            self.model.load_user_profile_data("general information")
            self.model.load_user_calorie_intake_history()
            self.model.load_all_history_data()
            self.model.load_specific_intake_data(helpers.get_date_today())

    def load_all_history_data(self):
        """Loads all the user history data in database."""
        self.views[0].loading_view.open()
        self.done_progress -= 1/self.no_of_parts
        self.model.load_all_history_data()

    def load_specific_intake_data(self, date_: str = helpers.get_date_today()):
        """Loads the intake data of the user at specific date."""
        self.views[0].loading_view.open()
        self.done_progress -= 1/self.no_of_parts
        self.model.load_specific_intake_data(date_)

    def show_connection_error(self):
        """Shows the connection error snackbar."""
        self.views[0].connection_error_snackbar.open()

    def hide_connection_error(self):
        """Hides the connection error snackbar."""
        self.views[0].connection_error_snackbar.dismiss()

    def done_loading(self, from_):
        """Closes the loading view if finish loading parts."""
        self.done_progress += 1/self.no_of_parts
        print(from_, self.done_progress)
        if self.done_progress >= 1.0:
            self.views[0].loading_view.dismiss()

    def update_user_profile_data(self, textfields: list):
        """Updates user data in database.

        Args:
            textfields (list): the list of textfields to get the new data.
        """
        self.views[0].loading_view.open()
        self.done_progress -= 1/self.no_of_parts
        height = float(textfields[1].text)
        weight = float(textfields[0].text)
        bmi_value = helpers.get_bmi_value(height, weight)
        bmi_classification = helpers.get_bmi_classification(bmi_value)
        user_input = {
            "Name": textfields[2].text,
            "Height": height,
            "Weight": weight,
            "BMI": bmi_classification,
            "BMI Value": bmi_value,
        }
        self.model.update_user_profile_data(user_input)

    def add_intake_to_database(self, user_input: list, calorie_goal: float):
        """Adds the food intake to the users history in database.

        Args:
            user_input (list): the list of user inputs to be stored.
            calorie_goal (float): the calorie goal to be updated.
        """
        self.views[0].loading_view.open()
        self.done_progress -= 1/self.no_of_parts
        date_today = helpers.get_date_today()
        user_input[0] = float(user_input[0])
        calorie_goal -= user_input[0]
        self.model.update_calorie_goal(round(calorie_goal, 1), f"History/{date_today}")
        self.model.add_intake_to_database(user_input)

    def delete_intake_to_database(self, checked_items: list, calorie_goal: float):
        """Deletes the food intake of the user in database.

        Args:
            calorie_screen (CalorieCounterScreenView): the calorie counter screen view.
            calorie_goal (float): the calorie goal to be updated.
        """
        self.views[0].loading_view.open()
        self.done_progress -= 1/self.no_of_parts
        date_today = helpers.get_date_today()
        calorie_goal += sum(item.calorie_amount for item in checked_items)
        self.model.update_calorie_goal(round(calorie_goal, 1), f"History/{date_today}")
        self.model.delete_intake_to_database(checked_items)

    def update_all_calorie_goal(self, new_activity: str):
        """Updates the base calorie goal and current calorie goal of the user.

        Args:
            new_activity (str): the new activity selected by the user.
        """
        self.views[0].loading_view.open()
        self.done_progress -= 1/self.no_of_parts
        date_today = helpers.get_date_today()
        user_data = self.model.user_profile_data

        # compute new calorie goal for the user information.
        bmr = helpers.get_user_bmr(
            user_data["Gender"], user_data["Weight"], user_data["Height"], user_data["Age"]
        )
        calorie_goal = helpers.calculate_calorie_goal(
            bmr, new_activity, user_data["Mode"], user_data["Intensity"]
        )
        self.model.update_user_profile_data({"Activity": new_activity})
        self.model.update_calorie_goal(float(calorie_goal), "UserInfo")

        # compute new calorie goal for the calorie counter screen
        for identifier, item in self.model.user_calorie_intake_data.items():
            if identifier != "Calorie Goal":
                calorie_goal -= Decimal(str(item["Calorie Amount"]))
        self.model.update_calorie_goal(float(calorie_goal), f"History/{date_today}")
