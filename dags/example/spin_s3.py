from airflow.decorators import dag, task
from airflow.utils.dates import days_ago
from airflow.providers.http.operators.http import HttpOperator
from airflow.providers.sftp.operators.sftp import SFTPOperator
from example.config import INPUT_FILE_NAME

@dag(schedule_interval=None, start_date=days_ago(1), catchup=False)
def spin_s3():
    get_file = SFTPOperator(
        task_id='get_file',
        ssh_conn_id='ftp_server',
        remote_filepath=INPUT_FILE_NAME,
        local_filepath=f'/tmp/{INPUT_FILE_NAME}',
        create_intermediate_dirs=True,
        operation='get'
    )

    @task
    def read_file():
        with open(f'/tmp/{INPUT_FILE_NAME}', 'rb') as file:
            return file.read().decode('utf-8')

    file_content = read_file()

    send_to_s3 = HttpOperator(
        task_id='place_in_s3',
        http_conn_id='spin_http',
        method='PUT',
        headers={'x-uri-path': INPUT_FILE_NAME},
        data="{{ ti.xcom_pull(task_ids='read_file') }}"
    )

    get_file >> file_content >> send_to_s3

spin_s3 = spin_s3()
