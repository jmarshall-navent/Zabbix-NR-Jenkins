import logging
import select
import subprocess

def zabbix_sender(key, output, server, hostname):
    """
    Sends a message to the Zabbix monitoring server to update the given key
    with the given output. This is designed to be only called whenever
    the service encounters an error.

    Zabbix should be configured with an Zabbix Trapper
    item for any key passed in, and a trigger for any instance where the output
    value of the message has a string length greater than 0. Since this method
    should only be called when something goes wrong, the Zabbix setup for
    listening for this key should be "any news is bad news"

    @param key
    The item key to use when communicating with Zabbix. This should match a key
    configured on the Zabbix server for the service.
    @param output
    The data to display in Zabbix notifying TechOps of a problem.

    """

    # When I actually did this at work, I had the server and hostname set in an
    # external configuration file. That's probably how you want to do this as
    # opposed to hard-coding it into the script.
    
    #los pongo como parametros
    #server = "zabbix-server-name"
    #hostname = "http://zabbix-server.com"

    cmd = "zabbix_sender -s " + server + " -z " + hostname + " -k " + key +\
            " -o \"" + output +"\""
    zabbix_send_is_running = lambda: zabbix_send_process.poll() is None

    zabbix_send_process = subprocess.Popen(cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            shell=True)

    error_buffer = ""

    # Submit a message with the given key and output information to the Zabbix
    # server.
    while zabbix_send_is_running():
        rlist, wlist, xlist = select.select([zabbix_send_process.stdout,
            zabbix_send_process.stderr],
            [],
            [],
            1)

        # Although the zabbix_send_process is grabbing data from both standard
        # output and standard error, really all we care about is standard
        # error.
        if zabbix_send_process.stderr in rlist:
            error_buffer += zabbix_send_process.stderr.read(1024)

    final_out, final_error = zabbix_send_process.communicate()

    # A return code of anything other than 0 means something went wrong. Log
    # an error and raise an exception.
    if zabbix_send_process.returncode != 0:
        logging.exception("Could not send message to Zabbix monitoring " +
                "server! The message was: %s" % (cmd))
        logging.exception(error_buffer + final_error)
        raise Exception("Could not send message to Zabbix server! Check " +
                "the logs for full details!")


import requests
id = 14102415
headerApiKey = 'ef374bb363b7bd9bae2f4a327c474e2554ab5206d34401e'
nameWebTTTSprCtl = 'WebTransactionTotalTime/SpringController/v0/empresas/avisos/ (GET)'
nameError = "Errors/WebTransaction/SpringController/v0/empresas/avisos/ (GET)"

r = requests.get('https://api.newrelic.com/v2/applications/' +str(id) + '/metrics/data.json', headers={'X-Api-Key':headerApiKey}, params={'names':nameWebTTTSprCtl})


average_response_time = 0
call_count = 0
error_count = 0
inc = 0

for item in r.json()['metric_data']['metrics'][0]['timeslices']:
	average_response_time += item['values']['average_response_time']
	call_count += item['values']['call_count']
	inc += 1


print "Tiempo promedio de respuesta: " + str(average_response_time/inc)
print "Total de llamados en los ultimos 30 minutos: " + str(call_count)

r2 = requests.get('https://api.newrelic.com/v2/applications/'+ str(id) + '/metrics/data.json', headers={'X-Api-Key':headerApiKey}, params={'names': nameError})

#for item in r2.json()['metric_data']['metrics_found']:
#	print item
#for item in r2.json()['metric_data']['metrics'][0]['timeslices']:
#	error_count += item['values']['error_count']

print "Total de errores: " + str(error_count)


#from pyzabbix import ZabbixMetric, ZabbixSender

# Send metrics to zabbix trapper
#packet = [
#  ZabbixMetric('NewRelic-api-jobs-produccion', 'test[average_response_time]', average_response_time),
#  ZabbixMetric('hostname1', 'test[system_status]', "OK"),
#]

#result = ZabbixSender(use_config=True).send(packet)*/

zabbix_sender('averageResponseTime', str(average_response_time), '192.168.4.1-254' , 'NewRelic-api-jobs-produccion')