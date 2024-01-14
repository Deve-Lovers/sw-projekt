"""
Projekt na systemy wbudowane: SKRZYZOWANIE
autorzy:
- Aleksandra Kozak 151870
- Jakub Lemiesiewicz 151922
"""
import time
import dataclasses
import Adafruit_BBIO.GPIO as GPIO

from enum import StrEnum
from threading import Thread


GREEN = "green"
YELLOW = "yellow"
RED = "red"
START_TIME = [8, 59, 30]  # [h, m, s]

X_LABEL = "x"
X_CAR_RED_LIGHT = "P8_7"
X_CAR_YELLOW_LIGHT = "P8_9"
X_CAR_GREEN_LIGHT = "P8_11"
X_PEOPLE_BLACK = "P8_15"
X_PEOPLE_YELLOW = "P8_17"

X_BUTTON_IN = "P9_41"
X_SENSOR_IN = "P8_26"

Y_LABEL = "y"
Y_CAR_RED_LIGHT = "P8_8"
Y_CAR_YELLOW_LIGHT = "P8_10"
Y_CAR_GREEN_LIGHT = "P8_12"

Y_PEOPLE_BLACK = "P8_16"
Y_PEOPLE_YELLOW = "P8_18"
Y_BUTTON_IN = "P9_12"
Y_SENSOR_IN = "P9_30"


def set_high(pin: str) -> None:
    """
    Funkcja ustawiająca dany pin w stan wysoki.
    """
    GPIO.output(pin, GPIO.HIGH)


def set_low(pin: str) -> None:
    """
    Funkcja ustawiająca dany pin w stan niski.
    """
    GPIO.output(pin, GPIO.LOW)


class CustomTime:
    """
    Klasa zegara aplikacji.
    """

    def __init__(self, h: int = START_TIME[0], m: int = START_TIME[1], s: int = START_TIME[2]):
        self.h = h
        self.m = m
        self.s = s

    def get_time(self) -> str:
        """
        Pobranie czasu w formacie String.
        """
        return f"{self.h}:{self.m}:{self.s}"

    def increment(self):
        """
        Metoda inkrementująca zegar.
        """
        self.s += 1

        if self.s == 60:
            self.s = 0
            self.m += 1

        if self.m == 60:
            self.m = 0
            self.h += 1

        if self.h == 24:
            self.h = 0

    def run(self):
        """
        Metoda uruchamiająca pracę zegara aplikacji.
        """
        while True:
            self.increment()
            time.sleep(1)

    def __str__(self) -> str:
        return self.get_time()

    @property
    def seconds(self):
        """
        Własność zwracająca czas w sekundach od godziny 00:00:00
        """
        return self.h * 60 * 60 + self.m * 60 + self.s

    def is_greater(self, another_time):
        """
        Metoda do porównywania czasu.
        """
        return another_time.seconds < self.seconds


timer: CustomTime = CustomTime()
stop_night: bool = False


def timedelta(h: int = 0, m: int = 0, s: int = 0) -> CustomTime:
    """
    Metoda do obliczania nowego czasu przesuniętego o argumenty funkcji.
    """
    fake_time = CustomTime(timer.h, timer.m, timer.s)
    seconds = h * 60 * 60 + m * 60 + s
    for i in range(seconds):
        fake_time.increment()
    return fake_time


def current_time(*args, **kwargs) -> CustomTime:
    """
    Metoda zwracająca kopię obiektu reprezentujący obecny czas pracy aplikacji.
    """
    return CustomTime(h=timer.h, m=timer.m, s=timer.s)


class SmallLight:
    def __init__(self, black: str, yellow: str, start: str) -> None:
        self.black = black
        self.yellow = yellow
        self._start(start)

    def _start(self, start):
        """
        Metoda uruchamiająca sygnalizator w zalezności od trybu drogi.
        """
        if start == GREEN:
            self.turn_on_green()
        elif start == RED:
            self.turn_on_red()

    def turn_off(self) -> None:
        """
        Metoda wyłączająca sygnalizator.
        """
        set_low(self.black)
        set_low(self.yellow)

    def turn_on_green(self) -> None:
        """
        Metoda włączająca światło zielone.
        """
        set_high(self.black)
        set_high(self.yellow)

    def turn_on_red(self) -> None:
        """
        Metoda włączająca światło czerwone.
        """
        set_high(self.black)
        set_low(self.yellow)

    def _blink_by_time(self, given_time: float, iterations: int) -> None:
        """
        Metoda do mrugania świateł na bazie argumentów.
        """
        for _ in range(iterations):
            self.turn_off()
            time.sleep(given_time)
            self.turn_on_green()
            time.sleep(given_time)

    def blinking(self) -> None:
        """
        Metoda do mrugania świateł przed przełączenia w tryb czerwony.
        """
        self._blink_by_time(0.35, 4)
        self._blink_by_time(0.25, 4)


class CarLight:
    """
    Klasa sygnalizatora drogowego dla samochodów.
    """

    def __init__(self, green: str, yellow: str, red: str, start: str) -> None:
        """
        Inicjalizator klasy sygnalizatora świetlego dla samochodów.
        """
        self.green = green
        self.yellow = yellow
        self.red = red
        self._start(start)

    def _setup(self):
        """
        Metoda wykonująca bezpieczny setup na start.
        """
        set_high(self.green)
        set_high(self.yellow)
        set_high(self.red)

    def _start(self, start: str) -> None:
        """
        Metoda uruchamiająca sygnalizator po przypisaniu pinów.
        """
        self._setup()
        if start == GREEN:
            self.setup_green()
        elif start == RED:
            self.setup_red()

    def blink_yellow(self) -> None:
        """
        Metoda uruchamiająca i podtrzymująca tryb nocny, dopóki nie zajdzie wywłaszczenie.
        Tryb nocny kończy się kiedy zmienna 'stop_night' przyjmie wartość True.
        """
        global stop_night
        stop_night = False
        set_high(self.green)
        set_high(self.red)

        while stop_night != True:
            print("(blink) (yellow)")
            set_low(self.yellow)
            time.sleep(0.5)
            set_high(self.yellow)
            time.sleep(0.5)

    def setup_red(self) -> None:
        """
        Metoda uruchamiająca światło czerwone na start działania sygnalizatora.
        """
        set_low(self.red)

    def setup_green(self) -> None:
        """
        Metoda uruchamiająca światło zielone na start działania sygnalizatora.
        """
        set_low(self.green)

    def make_red(self) -> None:
        """
        Metoda uruchamiająca światło czerwone.
        """
        set_high(self.green)
        set_low(self.yellow)
        time.sleep(1)
        set_high(self.yellow)
        set_low(self.red)

    def make_green(self) -> None:
        """
        Metoda uruchamiająca zielone światło. Najpierw zapala jednocześnie światło zółte,
        następnie gasi zółte i czerwone i zapala zielone
        """
        set_low(self.yellow)
        time.sleep(1)
        set_high(self.red)
        set_high(self.yellow)
        set_low(self.green)


class Mode(StrEnum):
    """
    Enum ze trybami jakie moze przyjąć droga.
    """

    cars = "cars"
    people = "people"
    night = "night"


@dataclasses.dataclass
class State:
    """
    Klasa przechowująca informacje o stanie danej drogi.
    """

    people_await: bool = False
    cars_await: bool = False
    last_car_time: CustomTime | None = None


class Button:
    def __init__(self, pin: str) -> None:
        self.pin = pin

    @property
    def is_pressed(self) -> bool:
        """
        Metoda słuząca do zwracania informacji o stanie przycisku. Jezeli jest wciśnięty zwraca True.
        """
        return GPIO.input(self.pin) == GPIO.HIGH


class Sensor:
    def __init__(self, pin: str) -> None:
        self.pin = pin

    @property
    def is_active(self) -> bool:
        """
        Metoda słuząca do zwracania informacji o czujniku przerwania wiązki. Zwraca True jeśli czujnik jest przerwany.
        """
        GPIO.setup(self.pin, GPIO.IN)
        return GPIO.input(self.pin) == GPIO.LOW


class Road:
    """
    Klasa pojedynczej drogi.
    """
    
    def __init__(
        self,
        label: str,
        mode: Mode,
        small_lights: SmallLight,
        car_light: CarLight,
        button: Button,
        sensor: Sensor,
    ) -> None:
        """
        Inicjalizator drogi, przechowujący informacje o trybie w którym obecnie działa droga. Znajdują
        się w nim równiez przypisania do świateł dla pieszych oraz drogowych, oraz powiązana przyciski / czujniki.
        """
        self.label = label
        self.mode = mode
        self.small_lights = small_lights
        self.car_light = car_light
        self.button = button
        self.sensor = sensor
        self.state = State()
        self.expropriation = False

    @property
    def state_view(self) -> str:
        return f"People await: {self.state.people_await} ; Cars await {self.state.cars_await} ; Expropriation {self.expropriation}" 

    def read_button(self) -> None:
        """
        Funkcja która nasłuchuje dany przycisk jezeli dana droga jest w trybie przepuszczania samochdów.
        Jeśli przycisk jest wciśnięty zostaje ustawiona zmienna informująca o oczekiwaniu pieszych.
        """
        while True:
            if self.mode == Mode.cars:
                if self.button.is_pressed:
                    self.state.people_await = True
            time.sleep(0.2)

    def read_sensor(self) -> None:
        """
        Zczytywanie danych z czujnika przerwania wiązki. Jeśli następuje przerwanie to zostaje zawsze
        nadpisany czas pojawienia się ostatniego auta: self.state.last_car_time = current_time()
        oraz jeśli obecnie droga przepuszcza pieszych to zostaje ustawiona właściwość, która informuje,
        ze samochody oczekują na czewonym świetle.
        """
        while True:

            if self.sensor.is_active:
                self.state.last_car_time = current_time()
                if self.mode != Mode.cars:
                    self.state.cars_await = True
            time.sleep(0.2)

    def read_all_states(self):
        """
        Funkcja uruchamiająca nasłuchwiwanie i zczytywanie danych z czujników przerwania wiązki
        oraz przycisków. Funkcja uruchamia dwa osobne wątki aby nie zatrzymywać pracy programu.
        """
        Thread(target=self.read_button).start()
        Thread(target=self.read_sensor).start()

    def cars_on(self) -> None:
        """
        Metoda do zmiany danej drogi z trybu dla pieszych w tryb dla samochodów. Metoda uruchamia
        mruganie świateł dla pieszych, nestępnie zapala im czerwone światło. W następnej kolejności
        zapala zielone światła samochodom.
        """
        self.small_lights.blinking()
        self.small_lights.turn_on_red()
        self.car_light.make_green()
        self.mode = Mode.cars

    def people_on(self) -> None:
        """
        Metoda do zmiany danej drogi z trybu dla samochodów w tryb dla pieszych. Metoda zapala
        samochodom czerwone światło a następnie włącza zielone światło pieszym.
        """
        thread = Thread(target=self.car_light.make_red)
        thread.start()
        thread.join()
        time.sleep(1)
        self.small_lights.turn_on_green()
        self.mode = Mode.people

    def set_night(self) -> None:
        """
        Metoda do przechodzenia w tryb nocny wszystkich świateł.
        """
        self.mode = Mode.night
        self.small_lights.turn_off()
        Thread(target=self.car_light.blink_yellow).start()

    def switch(self) -> None:
        """
        Metoda do zmiany trybu świateł.
        """
        if self.mode == Mode.cars:
            self.people_on()
        else:
            self.cars_on()

    def calculate_expropriation(self) -> None:
        """
        Metoda do ustawiania właściwości informującej czy dla danej drogi jest wywłaszczenie które oczekuje
        na zmianę trybu.
        """
        if self.mode == Mode.cars:
            if self.state.people_await == True:
                self.expropriation = True


    def clear_state(self) -> None:
        """
        Metoda do czyszczenia stanów klasy.
        """
        self.state.people_await = False
        self.state.cars_await = False
        self.state.last_car_time = None
        self.expropriation = False


class CrossRoads:
    """
    Klasa obsługująca drogi przekazane w zmiennej 'roads'
    """

    def __init__(self, roads: dict[str: Road]) -> None:
        """
        Inicjalizator klasy CrossRoads.
        """
        self.roads = roads
        self.last_switch: CustomTime = current_time()
        self.next_switch: CustomTime = self._calculate_next_switch
        self.night = False

    def clear_states(self):
        """
        Metoda do czyszczenia statusów we wszystkich powiązanych drogach.
        """
        for k, road in self.roads.items():
            Thread(target=road.clear_state).start()

    def start_day(self) -> None:
        """
        Metoda słuząca do rozpoczynania dnia po nocy.
        """
        global stop_night
        stop_night = True

        self.clear_states()
        self.roads[X_LABEL].mode = Mode.cars
        self.roads[Y_LABEL].mode = Mode.people

        for label in [X_LABEL, Y_LABEL]:
            self.roads[label].small_lights.turn_on_red()
            self.roads[label].car_light.setup_red()

        time.sleep(2)
        self.roads[Y_LABEL].small_lights.turn_on_green()
        self.roads[X_LABEL].car_light.make_green()
        time.sleep(2)

    def start_night(self) -> None:
        """
        Metoda rozpoczynająca noc.
        """
        self.clear_states()
        for k, road in self.roads.items():
            Thread(target=road.set_night).start()

    @property
    def _calculate_next_switch(self):
        """
        Metoda zwracająca czas do następnej zmiany trybu pracy świateł.
        """
        return timedelta(s=60)

    def _log(self):
        """
        Metoda słuąca do logowania aktualnych stanów dróg.
        """
        print(f"(log) Current time: {timer} Next switch: {self.next_switch}")
        for k, road in self.roads.items():
            print(f" - Road {k}: Mode: {road.mode}, Status: {road.state_view}")

    def _log_night(self):
        """
        Metoda logująca, ze obecnie skrzyzowanie jest w trybie nocnym.
        """
        print("(log) ---- NIGHT ----")

    def listen(self):
        """
        Metoda uruchamiająca nasłuchiwanie stanów powiązanych przycisków i czujników przerwania wiązki.
        """
        for k, road in self.roads.items():
            road.read_all_states()

    def _iteration(self) -> None:
        """
        Metoda do wywoływania akcji co iterację sprawdzenia stanów skrzyzowania.
        """
        for k, road in self.roads.items():
            Thread(target=road.calculate_expropriation).start()

    def switch(self):
        """
        Metoda do zmiany trygu kazdej powiązanej drogi w skrzyzowaniu.
        """
        self.clear_states()
        for k, road in self.roads.items():
            Thread(target=road.switch).start()
        self.clear_states()

    def get_force_switch(self) -> bool:
        """
        Metoda sprawdzająca, czy w obecnym stanie drogi wywierają wymuszenie.
        """
        if timer.seconds + 3 > self.next_switch.seconds:
            return False

        people_road = None
        cars_road = None
        for k, road in self.roads.items():
            if road.mode == Mode.cars:
                cars_road = road
            else:
                people_road = road

        if None not in [people_road, cars_road]:
            if people_road.state is not None:
                if people_road.state.cars_await:
                    if cars_road.state.last_car_time is None:
                        return True
                    if cars_road.state.last_car_time.seconds + 10 < timer.seconds:
                        return True

                if cars_road.state.people_await:
                    if cars_road.state.last_car_time is None:
                        return True
                    if cars_road.state.last_car_time.seconds + 10 < timer.seconds:
                        return True

        return False


    def process(self):
        """
        Główna metoda klasy CrossRoads, w której odbywa się cały proces iteracji skrzyzowania dróg.
        Metoda uruchamia proces nasłuchiwania stanów w przyciskach i czujnikach, oraz wchodzi w nieskończoną
        pętle działania skrzyzowania. Logika obsługuje przepinanie się w tryb nocny, obsługuje wywłaszczenia,
        oraz zmienia tryb świateł kiedy minie wskazany czas.
        """
        self.listen()
    
        while True:
            time.sleep(1)
            self._log()

            if self.night == True:
                self._log_night()
                if timer.h != 23:
                    if timer.seconds >= 5 * 60 * 60:
                        self.night = False
                        self.start_day()
            else:
                self._iteration()
                if self.get_force_switch() == True:
                    new_switch: CustomTime = timedelta(s=3)
                    if new_switch.seconds < self.next_switch.seconds:
                        self.next_switch = new_switch

                if timer.is_greater(self.next_switch):
                    print("SWITCH")
                    self.switch()
                    time.sleep(10)
                    self.roads[X_LABEL].clear_state()
                    self.roads[Y_LABEL].clear_state()
                    self.next_switch = self._calculate_next_switch

                if timer.seconds >= 23 * 60 * 60:
                    self.night = True
                    self.start_night()


def setup(*args, **kwargs) -> None:
    """
    Funkcja do setup'owania konkretnych pinów na BBB.
    """
    INPUTS = (
        X_BUTTON_IN, X_SENSOR_IN,
        Y_BUTTON_IN, Y_SENSOR_IN
    )
    OUTPUTS = (
        X_CAR_RED_LIGHT, X_CAR_YELLOW_LIGHT, X_CAR_GREEN_LIGHT, X_PEOPLE_BLACK, X_PEOPLE_YELLOW,
        Y_CAR_RED_LIGHT, Y_CAR_YELLOW_LIGHT, Y_CAR_GREEN_LIGHT, Y_PEOPLE_BLACK, Y_PEOPLE_YELLOW,
    )
    GPIO.cleanup()

    for pin in INPUTS:
        GPIO.setup(pin, GPIO.IN)
        print(f"GPIO.setup({pin}) INPUT")

    for pin in OUTPUTS:
        GPIO.setup(pin, GPIO.OUT)
        print(f"GPIO.setup({pin}) OUTPUT")


def main(*args, **kwargs) -> None:
    """
    Funkcja main.
    """
    # setup BBB
    setup()

    set_high(X_CAR_GREEN_LIGHT)
    set_high(X_CAR_YELLOW_LIGHT)
    set_high(X_CAR_RED_LIGHT)
    set_high(Y_CAR_GREEN_LIGHT)
    set_high(Y_CAR_YELLOW_LIGHT)
    set_high(Y_CAR_RED_LIGHT)

    # setup timer
    thread = Thread(target=timer.run)
    thread.start()

    x_people_light1 = SmallLight(black=X_PEOPLE_BLACK, yellow=X_PEOPLE_YELLOW, start=RED)
    x_car_light1 = CarLight(green=X_CAR_GREEN_LIGHT, yellow=X_CAR_YELLOW_LIGHT, red=X_CAR_RED_LIGHT, start=GREEN)
    x_button = Button(pin=X_BUTTON_IN)
    x_sensor = Sensor(pin=X_SENSOR_IN)

    y_people_light1 = SmallLight(black=Y_PEOPLE_BLACK, yellow=Y_PEOPLE_YELLOW, start=GREEN)
    y_car_light1 = CarLight(green=Y_CAR_GREEN_LIGHT, yellow=Y_CAR_YELLOW_LIGHT, red=Y_CAR_RED_LIGHT, start=RED)
    y_button = Button(pin=Y_BUTTON_IN)
    y_sensor = Sensor(pin=Y_SENSOR_IN)

    x_road = Road(
        label=X_LABEL,
        mode=Mode.cars,
        small_lights=x_people_light1,
        car_light=x_car_light1,
        button=x_button,
        sensor=x_sensor
    )

    y_road = Road(
        label=Y_LABEL,
        mode=Mode.people,
        small_lights=y_people_light1,
        car_light=y_car_light1,
        button=y_button,
        sensor=y_sensor
    )

    cr = CrossRoads(roads={X_LABEL: x_road, Y_LABEL: y_road})
    cr.process()


if __name__ == "__main__":
    main()
