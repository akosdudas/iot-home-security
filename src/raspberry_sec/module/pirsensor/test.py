import os, sys, time
from multiprocessing import Event, process
from threading import Thread

sys.path.append(os.path.join(os.path.dirname(__file__), '../../..'))
from raspberry_sec.module.pirsensor.producer import PirsensorProducer
from raspberry_sec.module.pirsensor.consumer import PirsensorConsumer, ConsumerContext
from raspberry_sec.system.util import ProcessContext
from raspberry_sec.interface.producer import ProducerDataProxy, ProducerDataManager
from raspberry_sec.system.hw_util import check_platform, is_gpio_floating

def set_producer_parameters():
    parameters = dict()
    parameters['GPIO_PIR'] = 7
    parameters['wait_interval'] = 1
    return parameters

def set_consumer_parameters():
    parameters = dict()
    parameters['timeout'] = 1
    return parameters

def setup_context(proxy: ProducerDataProxy, stop_event: Event):
    return ProcessContext(
        log_queue=None,
        stop_event=stop_event,
        shared_data_proxy=proxy
    )

def show_motion_status(context: ProcessContext):
    data_proxy = context.get_prop('shared_data_proxy')
    consumer = PirsensorConsumer(set_consumer_parameters())
    consumer_context = ConsumerContext(None, False)
    try:
        while not context.stop_event.is_set():
            consumer_context.data = data_proxy.get_data()
            results = consumer.run(consumer_context)
            print(f'Consumer run - ALERT: {results.alert} - DATA: {results.data}')
    finally:
        pass

def finish(stop_event: Event):
    input('Please press enter to exit...')
    stop_event.set()
    time.sleep(1)

def integration_test():
    # The integration test of the PIR sensor only makes sense when run on a RPi
    if not check_platform():
        raise OSError('This integration test must be run on a Raspberry Pi')
    
    producer = PirsensorProducer(set_producer_parameters())

    producer.register_shared_data_proxy()
    manager = ProducerDataManager()
    manager.start()
    proxy = producer.create_shared_data_proxy(manager)

    stop_event = Event()
    stop_event.clear()

    producer_process_context = setup_context(proxy, stop_event)
    consumer_process_context = setup_context(proxy, stop_event)

    Process(target=producer.run, args=(producer_process_context,)).start()
    Thread(target=finish, args=(stop_event,)).start()

    show_motion_status(consumer_process_context)

if __name__ == "__main__":
    integration_test()
