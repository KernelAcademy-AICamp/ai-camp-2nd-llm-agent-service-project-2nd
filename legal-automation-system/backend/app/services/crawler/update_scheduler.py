"""
법률 데이터 업데이트 스케줄러
"""

import asyncio
from typing import Optional, List, Dict, Any
from datetime import datetime, timedelta
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from apscheduler.triggers.interval import IntervalTrigger

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, func

from app.core.config import settings
from app.core.logging import logger
from app.database.session import get_db
from app.models.law import Law, LawCase, LawUpdate
from app.services.crawler.law_crawler import KoreanLawCrawler, LawCategoryManager
from app.services.crawler.case_crawler import CaseCrawler
from app.services.rag.retriever import LegalRAGSystem


class UpdateScheduler:
    """법률 데이터 업데이트 스케줄러"""

    def __init__(self):
        """스케줄러 초기화"""
        self.scheduler = AsyncIOScheduler()
        self.law_crawler = None
        self.case_crawler = None
        self.rag_system = LegalRAGSystem()

        # 작업 설정
        self.jobs = {
            'daily_law_update': {
                'func': self.update_laws,
                'trigger': CronTrigger(hour=2, minute=0),  # 매일 새벽 2시
                'name': 'Daily Law Update'
            },
            'weekly_case_update': {
                'func': self.update_cases,
                'trigger': CronTrigger(day_of_week='sun', hour=3, minute=0),  # 매주 일요일 새벽 3시
                'name': 'Weekly Case Update'
            },
            'hourly_quick_check': {
                'func': self.quick_update_check,
                'trigger': IntervalTrigger(hours=1),  # 매시간
                'name': 'Hourly Quick Check'
            },
            'monthly_full_crawl': {
                'func': self.full_crawl,
                'trigger': CronTrigger(day=1, hour=4, minute=0),  # 매월 1일 새벽 4시
                'name': 'Monthly Full Crawl'
            },
            'index_optimization': {
                'func': self.optimize_indexes,
                'trigger': CronTrigger(hour=5, minute=0),  # 매일 새벽 5시
                'name': 'Index Optimization'
            }
        }

        # 통계
        self.stats = {
            'last_update': None,
            'laws_updated': 0,
            'cases_updated': 0,
            'errors': 0,
            'last_error': None
        }

    def start(self):
        """스케줄러 시작"""
        try:
            # 작업 등록
            for job_id, job_config in self.jobs.items():
                self.scheduler.add_job(
                    job_config['func'],
                    job_config['trigger'],
                    id=job_id,
                    name=job_config['name'],
                    replace_existing=True,
                    max_instances=1
                )

            # 스케줄러 시작
            self.scheduler.start()
            logger.info("Update scheduler started")

            # 초기화 작업
            asyncio.create_task(self.initialize())

        except Exception as e:
            logger.error(f"Scheduler start error: {e}")
            raise

    def stop(self):
        """스케줄러 중지"""
        if self.scheduler.running:
            self.scheduler.shutdown(wait=False)
            logger.info("Update scheduler stopped")

    async def initialize(self):
        """초기화 작업"""
        async for db in get_db():
            try:
                # 카테고리 초기화
                category_manager = LawCategoryManager()
                await category_manager.initialize_categories(db)

                # 초기 크롤링 필요 여부 확인
                stmt = select(func.count(Law.id))
                result = await db.execute(stmt)
                law_count = result.scalar()

                if law_count == 0:
                    logger.info("No laws found, starting initial crawl")
                    await self.initial_crawl(db)

            except Exception as e:
                logger.error(f"Initialization error: {e}")
            finally:
                await db.close()

    async def initial_crawl(self, db: AsyncSession):
        """초기 크롤링"""
        logger.info("Starting initial law crawl")

        async with KoreanLawCrawler() as crawler:
            # 주요 법률 크롤링 (제한적으로)
            laws = await crawler.crawl_all_laws(limit=1000)
            await crawler.save_to_database(laws, db)

        async with CaseCrawler() as crawler:
            # 최근 판례 크롤링
            cases = await crawler.crawl_recent_cases(limit=100)
            await crawler.save_cases_to_database(cases, db)

        logger.info(f"Initial crawl completed: {len(laws)} laws, {len(cases)} cases")

    async def update_laws(self):
        """법률 업데이트"""
        async for db in get_db():
            try:
                logger.info("Starting law update")
                start_time = datetime.now()

                async with KoreanLawCrawler() as crawler:
                    # 최근 업데이트된 법률 확인
                    await crawler.update_laws(db)

                    # 통계 업데이트
                    self.stats['last_update'] = datetime.now()
                    self.stats['laws_updated'] += 1

                elapsed = (datetime.now() - start_time).total_seconds()
                logger.info(f"Law update completed in {elapsed:.2f} seconds")

            except Exception as e:
                logger.error(f"Law update error: {e}")
                self.stats['errors'] += 1
                self.stats['last_error'] = str(e)
            finally:
                await db.close()

    async def update_cases(self):
        """판례 업데이트"""
        async for db in get_db():
            try:
                logger.info("Starting case update")
                start_time = datetime.now()

                async with CaseCrawler() as crawler:
                    # 최근 판례 크롤링
                    cases = await crawler.crawl_recent_cases(limit=50)
                    await crawler.save_cases_to_database(cases, db)

                    # 법령해석 크롤링
                    interpretations = await crawler.crawl_law_interpretations(limit=30)
                    await crawler.save_interpretations_to_database(interpretations, db)

                    self.stats['cases_updated'] += len(cases)

                elapsed = (datetime.now() - start_time).total_seconds()
                logger.info(f"Case update completed in {elapsed:.2f} seconds")

            except Exception as e:
                logger.error(f"Case update error: {e}")
                self.stats['errors'] += 1
                self.stats['last_error'] = str(e)
            finally:
                await db.close()

    async def quick_update_check(self):
        """빠른 업데이트 확인"""
        async for db in get_db():
            try:
                # 최근 1시간 이내 업데이트 확인
                one_hour_ago = datetime.now() - timedelta(hours=1)

                stmt = select(LawUpdate).where(
                    LawUpdate.created_at > one_hour_ago
                ).limit(10)

                result = await db.execute(stmt)
                updates = result.scalars().all()

                if updates:
                    logger.info(f"Found {len(updates)} recent updates")

                    # 긴급 업데이트 처리
                    for update in updates:
                        if update.update_type in ['긴급', '중요']:
                            await self._process_urgent_update(update, db)

            except Exception as e:
                logger.error(f"Quick check error: {e}")
            finally:
                await db.close()

    async def full_crawl(self):
        """전체 크롤링 (월 1회)"""
        async for db in get_db():
            try:
                logger.info("Starting monthly full crawl")
                start_time = datetime.now()

                async with KoreanLawCrawler() as crawler:
                    # 모든 카테고리 전체 크롤링
                    laws = await crawler.crawl_all_laws(limit=5000)
                    await crawler.save_to_database(laws, db)

                async with CaseCrawler() as crawler:
                    # 대량 판례 크롤링
                    cases = await crawler.crawl_recent_cases(limit=500)
                    await crawler.save_cases_to_database(cases, db)

                elapsed = (datetime.now() - start_time).total_seconds() / 60
                logger.info(f"Full crawl completed in {elapsed:.2f} minutes")

            except Exception as e:
                logger.error(f"Full crawl error: {e}")
                self.stats['errors'] += 1
                self.stats['last_error'] = str(e)
            finally:
                await db.close()

    async def optimize_indexes(self):
        """인덱스 최적화"""
        try:
            logger.info("Starting index optimization")

            # Pinecone 인덱스 최적화
            # 오래된 벡터 정리
            await self._cleanup_old_vectors()

            # 중복 벡터 제거
            await self._remove_duplicate_vectors()

            # 인덱스 통계 갱신
            await self._update_index_stats()

            logger.info("Index optimization completed")

        except Exception as e:
            logger.error(f"Index optimization error: {e}")

    async def _process_urgent_update(self, update: LawUpdate, db: AsyncSession):
        """긴급 업데이트 처리"""
        try:
            logger.info(f"Processing urgent update: {update.law_id}")

            async with KoreanLawCrawler() as crawler:
                # 특정 법률 재크롤링
                detail_data = await crawler._fetch_law_detail(update.law_id, "")
                if detail_data:
                    await crawler.save_to_database(detail_data, db)

                    # RAG 시스템 즉시 업데이트
                    for law_data in detail_data:
                        law = Law(**law_data)
                        await self.rag_system.index_law(law)

        except Exception as e:
            logger.error(f"Urgent update processing error: {e}")

    async def _cleanup_old_vectors(self):
        """오래된 벡터 정리"""
        try:
            # 6개월 이상 된 벡터 확인
            six_months_ago = datetime.now() - timedelta(days=180)

            # Pinecone에서 메타데이터 기준으로 필터링
            # (실제 구현은 Pinecone API에 따라 다름)
            logger.info("Cleaning up old vectors")

        except Exception as e:
            logger.error(f"Vector cleanup error: {e}")

    async def _remove_duplicate_vectors(self):
        """중복 벡터 제거"""
        try:
            # 중복 검사 및 제거 로직
            logger.info("Removing duplicate vectors")

        except Exception as e:
            logger.error(f"Duplicate removal error: {e}")

    async def _update_index_stats(self):
        """인덱스 통계 갱신"""
        try:
            # Pinecone 인덱스 통계 조회
            stats = self.rag_system.index.describe_index_stats()
            logger.info(f"Index stats: {stats}")

        except Exception as e:
            logger.error(f"Stats update error: {e}")

    def get_stats(self) -> Dict[str, Any]:
        """통계 조회"""
        return {
            'scheduler_running': self.scheduler.running,
            'jobs': [
                {
                    'id': job.id,
                    'name': job.name,
                    'next_run': job.next_run_time.isoformat() if job.next_run_time else None
                }
                for job in self.scheduler.get_jobs()
            ],
            'update_stats': self.stats
        }

    async def force_update(self, update_type: str = "all"):
        """강제 업데이트"""
        logger.info(f"Forcing update: {update_type}")

        if update_type in ["all", "laws"]:
            await self.update_laws()

        if update_type in ["all", "cases"]:
            await self.update_cases()

        if update_type == "full":
            await self.full_crawl()

        logger.info("Force update completed")


class CrawlerMonitor:
    """크롤러 모니터링"""

    def __init__(self):
        """모니터 초기화"""
        self.metrics = {
            'total_crawled': 0,
            'success_rate': 0.0,
            'average_time': 0.0,
            'errors': []
        }

    async def log_crawl_result(
        self,
        crawl_type: str,
        success: bool,
        duration: float,
        error: Optional[str] = None
    ):
        """크롤링 결과 로깅"""
        self.metrics['total_crawled'] += 1

        if success:
            # 성공률 업데이트
            success_count = self.metrics['success_rate'] * (self.metrics['total_crawled'] - 1)
            self.metrics['success_rate'] = (success_count + 1) / self.metrics['total_crawled']
        else:
            # 실패 기록
            if error:
                self.metrics['errors'].append({
                    'type': crawl_type,
                    'error': error,
                    'timestamp': datetime.now().isoformat()
                })

                # 최근 100개 에러만 유지
                if len(self.metrics['errors']) > 100:
                    self.metrics['errors'] = self.metrics['errors'][-100:]

        # 평균 시간 업데이트
        total_time = self.metrics['average_time'] * (self.metrics['total_crawled'] - 1)
        self.metrics['average_time'] = (total_time + duration) / self.metrics['total_crawled']

    def get_metrics(self) -> Dict[str, Any]:
        """메트릭 조회"""
        return self.metrics

    async def check_health(self) -> Dict[str, Any]:
        """헬스 체크"""
        health = {
            'status': 'healthy',
            'issues': []
        }

        # 성공률 확인
        if self.metrics['success_rate'] < 0.8:
            health['status'] = 'degraded'
            health['issues'].append(f"Low success rate: {self.metrics['success_rate']:.2%}")

        # 평균 시간 확인
        if self.metrics['average_time'] > 30:  # 30초 이상
            health['issues'].append(f"Slow crawling: {self.metrics['average_time']:.2f}s average")

        # 최근 에러 확인
        recent_errors = [e for e in self.metrics['errors']
                        if datetime.fromisoformat(e['timestamp']) > datetime.now() - timedelta(hours=1)]

        if len(recent_errors) > 10:
            health['status'] = 'unhealthy'
            health['issues'].append(f"Too many recent errors: {len(recent_errors)}")

        return health