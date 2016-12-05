import logging
import select
import subprocess
import datetime
import time
import io
import os

#def zabbix_sender(key, output, server, hostname, timestamp):
def zabbix_sender(server, hostname, input_file):
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

    #cmd = "zabbix_sender -z " + server + " -s " + hostname +"--with-timestamps " + timestamp + " -k " + key +\
    #        " -o \"" + output +"\""

    cmd = "zabbix_sender -z  " + server + " -s " + hostname + " -T -r -i " + input_file 

    print cmd

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
from requests.utils import quote


def makeNRInsightsAndSend(endpointSuffix, hostname, appName):
    queryApiKey = 'oFd67cCnqPSlKnO1B0Fge-3YpBA4OyPs'
    endpointSuffix = quote(endpointSuffix, safe='')

    #endpoint = 'https://insights-api.newrelic.com/v1/accounts/1233785/query?nrql=SELECT%20percentile%28databaseDuration%20%2a%201000%2C%2070%2C%2095%2C%2099%29%2C%20average%28databaseDuration%29%20%2a%201000%20as%20prom%2C%20max%28databaseDuration%29%20%2a%201000%20as%20max%2C%20stddev%28databaseDuration%29%20%2a%201000%20as%20std%20%2C%20min%28timestamp%29%20as%20timestamp%20FROM%20%20Transaction%20FACET%20name%20SINCE%201%20day%20ago%20where%20appName%20%3D%20%27api-jobs-produccion%27%20and%20name%20%3D%20%27WebTransaction%2FSpringController%2Fv0%2F'
    #
    #
    #Esta dentro del endpoint que app es. En este caso esta     apijobsProduccion  que seria id 14102415
    #
    endpoint = 'https://insights-api.newrelic.com/v1/accounts/1233785/query?nrql=SELECT%20percentile%28duration%20%2a%201000%2C%2070%2C%2095%2C%2099%29%2C%20average%28duration%29%20%2a%201000%20as%20prom%2C%20max%28duration%29%20%2a%201000%20as%20max%2C%20stddev%28duration%29%20%2a%201000%20as%20std%20%2C%20min%28timestamp%29%20as%20timestamp%20FROM%20%20Transaction%20FACET%20name%20SINCE%201%20day%20ago%20where%20appName%20%3D%20%27' + appName + '%27%20and%20name%20%3D%20%27WebTransaction%2FSpringController%2Fv0%2F'

    endpoint = endpoint + endpointSuffix + '%27'
    
    r = requests.get(endpoint, headers={'X-Query-Key': queryApiKey})
    
    jsonPercentiles = r.json()['totalResult']['results'][0]['percentiles']
    p99 = jsonPercentiles['99']
    p95 = jsonPercentiles['95']
    p70 = jsonPercentiles['70']

    dateTimeActual = datetime.datetime.now()



    dateTimeAnterior = dateTimeActual - datetime.timedelta(days=1)

    dateTimeAnterior = str(dateTimeAnterior).replace('', '')[:-7].upper()


    timestamp = int(time.mktime(datetime.datetime.strptime(str(dateTimeAnterior), "%Y-%m-%d %H:%M:%S").timetuple()))

    
    io.FileIO("foobar.txt", "a").write(hostname + ' avg_percentile_99 ' +  str(timestamp) + ' ' + str(p99) + ' \n')
    io.FileIO("foobar.txt", "a").write(hostname + ' avg_percentile_95 ' +  str(timestamp) + ' ' + str(p95) + ' \n')
    io.FileIO("foobar.txt", "a").write(hostname + ' avg_percentile_70 ' +  str(timestamp) + ' ' + str(p70) + ' \n')

    zabbix_sender('zabbix.bumeran.biz', hostname, 'foobar.txt')
    os.remove("foobar.txt")

def makeRequestAndZabbixSender(endpointName, hostname, id):
    

    headerApiKey = 'ef374bb363b7bd9bae2f4a327c474e2554ab5206d34401e'
    nameWebTTTSprCtl = 'WebTransactionTotalTime/SpringController/v0/' + endpointName 
    nameError = 'Errors/WebTransaction/SpringController/v0/' + endpointName

    dateTimeActual = datetime.datetime.now()
    dateTimeActual = dateTimeActual.replace(minute=0, second=0)


    dateTimeAnterior = dateTimeActual - datetime.timedelta(days=1)



    r = requests.get('https://api.newrelic.com/v2/applications/' +str(id) + '/metrics/data.json', headers={'X-Api-Key':headerApiKey}, params={'names':nameWebTTTSprCtl,'from':dateTimeAnterior,'to':dateTimeActual, 'values':'average_response_time'})

    for item in r.json()['metric_data']['metrics'][0]['timeslices']:
    	average_response_time = item['values']['average_response_time']
    	timestamp = item['from']
    	timestamp = timestamp.replace(' ', '')[:-7].upper()
    	timestamp = int(time.mktime(datetime.datetime.strptime(timestamp, "%Y-%m-%dT%H:%M:%S").timetuple()))
    	io.FileIO("foobar.txt", "a").write(hostname + ' average_response_time ' +  str(timestamp) + ' ' + str(average_response_time) + ' \n')
    	#zabbix_sender('zabbix.bumeran.biz', hostname, 'foobar.txt')
    	#call_count = item['values']['call_count']
    
    zabbix_sender('zabbix.bumeran.biz', hostname, 'foobar.txt')
    os.remove("foobar.txt")

    r2 = requests.get('https://api.newrelic.com/v2/applications/'+ str(id) + '/metrics/data.json', headers={'X-Api-Key':headerApiKey}, params={'names': nameError, 'from':dateTimeAnterior,'to':dateTimeActual})

    if (len(r2.json()['metric_data']['metrics_not_found']) != 0):
        print "no hay data"
        return 
    print "Si haty data"
    for item in r2.json()['metric_data']['metrics'][0]['timeslices']:
    	error_count = item['values']['error_count']
    	timestamp = item['from']
    	timestamp = timestamp.replace(' ', '')[:-7].upper()
    	timestamp = int(time.mktime(datetime.datetime.strptime(timestamp, "%Y-%m-%dT%H:%M:%S").timetuple()))
    	io.FileIO("foobar.txt", "a").write(hostname + ' error_count ' +  str(timestamp) + ' ' + str(error_count) + ' \n')

    zabbix_sender('zabbix.bumeran.biz', hostname, 'foobar.txt')
    os.remove("foobar.txt")


#apijobsProduccion
idApiJobs = 14102415
bm = 'api-jobs-produccion'
#api-jobs-zj-produccion
idZJ = 15119756
zj = 'api-jobs-zj-produccion'

makeRequestAndZabbixSender('empresas/avisos/ (GET)', 'ZJ-NR-EmpresasAvisos', idZJ)
makeRequestAndZabbixSender('empresas/curriculums/ (GET)', 'ZJ-NewRelic-EmpresasCV', idZJ)
makeRequestAndZabbixSender('empresas/avisos/{avisoId}/postulaciones (GET)', 'ZJ-NewRelic-EmpresasAvisoPostulaciones', idZJ)
makeRequestAndZabbixSender('application/avisos/search (POST)', 'ZJ-NewRelic-AplicacionAvisosSearch', idZJ)


makeNRInsightsAndSend('empresas/curriculums/ (GET)', 'ZJ-NewRelic-EmpresasCV', zj)
makeNRInsightsAndSend('empresas/avisos/{avisoId}/postulaciones (GET)', 'ZJ-NewRelic-EmpresasAvisoPostulaciones', zj)
makeNRInsightsAndSend('empresas/avisos/ (GET)', 'ZJ-NR-EmpresasAvisos', zj)
makeNRInsightsAndSend('application/avisos/search (POST)', 'ZJ-NewRelic-AplicacionAvisosSearch', zj)



makeRequestAndZabbixSender('empresas/avisos/ (GET)', 'NR-EmpresasAvisos', idApiJobs)
makeRequestAndZabbixSender('empresas/curriculums/ (GET)', 'NewRelic-EmpresasCV', idApiJobs)
makeRequestAndZabbixSender('empresas/avisos/{avisoId}/postulaciones (GET)', 'NewRelic-EmpresasAvisoPostulaciones', idApiJobs)
makeRequestAndZabbixSender('application/avisos/search (POST)', 'NewRelic-AplicacionAvisosSearch', idApiJobs)

makeNRInsightsAndSend('empresas/curriculums/ (GET)', 'NewRelic-EmpresasCV', bm)
makeNRInsightsAndSend('empresas/avisos/{avisoId}/postulaciones (GET)', 'NewRelic-EmpresasAvisoPostulaciones', bm)
makeNRInsightsAndSend('empresas/avisos/ (GET)', 'NR-EmpresasAvisos', bm)
makeNRInsightsAndSend('application/avisos/search (POST)', 'NewRelic-AplicacionAvisosSearch', bm)
