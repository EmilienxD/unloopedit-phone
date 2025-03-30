from personal_modules.display import Logger

from personal_modules.IP_rotation.VPN import VPN

from lib.planning import Planning

raise NotImplementedError
def main():
    with Logger('[AUTOMATION]') as logger:
        logger.info('Starting automation...')
        try:
            with Planning.from_accounts(plan_futur_days=0) as planning:
                #with VPN():
                logger.info('Executing plans...')
                plan = planning.oldest_incomplete_day_plan
                while plan is not None:
                    plan.execute_tasks()
                    # current plan will be completed if all its tasks are completed successfully
                    plan = planning.oldest_incomplete_day_plan
                logger.info('Done')
            logger.info('Automation finished successfully.')

        except KeyboardInterrupt:
            raise KeyboardInterrupt
        except Exception as e:
            logger.error(f'A fatal error occurred: {e}', skippable=False, base_error=e)

if __name__ == '__main__':
    main()

"""
,
        "T06_create_texts": {
            "enabled": false,
            "min_target_value": 5,
            "settings": {
                "target_languages": [
                    "english",
                    "french"
                ]
            }
        }
"""