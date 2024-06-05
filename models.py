import typing


# Es el modelo que genera un individuo backtest, el cual será parte de la población y luego será
# tomado en cuenta o descartado cuando sea comparado con otros individuos backtest en la optimización.
class BacktestResult:
    def __init__(self):
        self.pnl: float = 0.0
        self.max_dd: float = 0.0
        self.parameters: typing.Dict = dict()
        self.dominated_by: int = 0
        self.dominates: typing.List[int] = []
        self.rank: int = 0
        self.crowding_distance: float = 0.0

    # hace que cuando se imprime un objeto de la clase BacktestResult, se imprima con este formato
    def __repr__(self):
        return f"PNL = {round(self.pnl,2)} Max. Drawdown = {round(self.max_dd,2)} Parameters = {self.parameters} " \
               f"Rank = {self.rank} Crowding distance = {self.crowding_distance}"

    # reinicia el modelo a sus valores originales para ser reutilizado
    def reset_results(self):
        self.dominated_by = 0
        self.dominates.clear()
        self.rank = 0
        self.crowding_distance = 0.0


