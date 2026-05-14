from src.repositories.rolling_stock import RollingStockRepository
from src.repositories.catalogs import RegulationRepository, PartRepository, BrigadeRepository
from src.repositories.repair_tasks import RepairTaskRepository
from src.repositories.repair_stage import RepairStageRepository
from src.repositories.users import UserRepository


class DBManager:

    def __init__(self, session_factory):
        self.session_factory = session_factory

    async def __aenter__(self):
        self.session = self.session_factory()
        self.trains = RollingStockRepository(self.session)
        self.tasks = RepairTaskRepository(self.session)
        self.stages = RepairStageRepository(self.session)
        self.regulations = RegulationRepository(self.session)
        self.parts = PartRepository(self.session)
        self.brigades = BrigadeRepository(self.session)
        self.users = UserRepository(self.session)

        return self

    async def __aexit__(self, *args):
        await self.session.rollback()
        await self.session.close()

    async def commit(self):
        await self.session.commit()


