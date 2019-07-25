#
#
# expliot - Internet Of Things Security Testing and Exploitation Framework
#
# Copyright (C) 2019  Aseem Jakhar
#
# Email:   aseemjakhar@gmail.com
# Twitter: @aseemjakhar
#
# THIS SOFTWARE IS PROVIDED ``AS IS'' AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING,
# BUT NOT LIMITED TO, THE IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A
# PARTICULAR PURPOSE ARE DISCLAIMED.  IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS
# BE LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL
# DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES;
# LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON ANY
# THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING NEGLIGENCE
# OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE
# POSSIBILITY OF SUCH DAMAGE.
#

from expliot.core.tests.test import *
from expliot.core.protocols.internet.dicom import (
    AE,
    Dataset,
    QueryRetrievePresentationContexts,
    BasicWorklistManagementPresentationContexts
)

class CFind(Test):

    def __init__(self):
        super().__init__(name     = "c-find",
                         summary  = "DICOM Data Finder",
                         descr    = """This test case sends a C-FIND message i.e. sends a query for a patient name
                                       to the DICOM server (SCP - Service class Provider) and shows the retrieved
                                       details.""",
                         author   = "Aseem Jakhar",
                         email    = "aseemjakhar@gmail.com",
                         ref      = ["https://www.dicomstandard.org/current/",
                                     "http://dicom.nema.org/MEDICAL/dicom/2016a/output/chtml/part07/sect_9.3.2.html"],
                         category = TCategory(TCategory.DICOM, TCategory.SW, TCategory.ANALYSIS),
                         target   = TTarget(TTarget.GENERIC, TTarget.GENERIC, TTarget.GENERIC))

        self.argparser.add_argument('-r', '--rhost', required=True,
                                    help="Hostname/IP address of the target DICOM Server (SCP)")
        self.argparser.add_argument('-p', '--rport', default=104, type=int,
                                    help="Port number of the target DICOM Server (SCP). Default is 104")
        self.argparser.add_argument('-q', '--lport', default=0, type=int,
                                    help="If specified use this as the source/local port number for expliot")
        self.argparser.add_argument('-n', '--name', default="*",
                                    help="""Specify the patient name to search. Pleas note you can use 
                                            wild cards like * ? as mentioned in
                                            http://dicom.nema.org/MEDICAL/dicom/2016a/output/chtml/part04/sect_C.2.2.2.html""")
        self.argparser.add_argument('-c', '--aetscu', default="ANY-SCU",
                                    help="""Application Entity Title (AET) of Service Class User (SCU) i.e. the 
                                            calling AET(client/expliot). Default is \"ANY-SCU\" string""")
        self.argparser.add_argument('-s', '--aetscp', default="ANY-SCP",
                                    help="""Application Entity Title (AET) of Service Class Provider (SCP) i.e. the 
                                            called AET(DICOM server). Default is \"ANY-SCP\" string.""")
        #self.argparser.add_argument('-c', '--pcontext', default="1.2.840.10008.5.1.4.1.2.1.1",
        #                            help="""Presentation Context SOP class UID to use for C-FIND. Default is
        #                                    1.2.840.10008.5.1.4.1.2.1.1 (Ref: https://www.dicomlibrary.com/dicom/sop/)
        #                                    (Patient Root Query/Retrieve Information Model UID - FIND). If the above
        #                                    doesn't work then try others from the Ref page for example Study Root.
        #                                    (hint: search for FIND).""")
        self.argparser.add_argument('-m', '--model', default="P",
                                    help="""Specify the information model to use for C-FIND. Options are P, S, W and O
                                            for patient root, study root, modality worklist and patient/study only 
                                            (retired) respectively. Default is P""")

    def execute(self):

        TLog.generic("Attempting to search for patient ({}) on DICOM server ({}) on port ({})".format(self.args.name,
                                                                                                      self.args.rhost,
                                                                                                      self.args.rport))
        TLog.generic("Using Calling AET ({}) Called AET ({}) Information model ({})".format(self.args.aetscu,
                                                                                            self.args.aetscp,
                                                                                            self.args.model))
        assoc = None
        try:
            ae = AE(ae_title=self.args.aetscu)
            ae.requested_contexts = (QueryRetrievePresentationContexts + BasicWorklistManagementPresentationContexts)
            ds = Dataset()
            ds.PatientName = self.args.name
            # XXX May need to move this as cmdline argument for other SOP Class UIDs
            ds.QueryRetrieveLevel = 'PATIENT'
            # 0 means assign random port in pynetdicom
            if self.args.lport != 0:
                TLog.generic("Using source port number ({})".format(self.args.lport))
                if (self.args.lport < 1024) and (geteuid() != 0):
                    TLog.fail("Oops! Need to run as root for privileged port")
                    raise ValueError("Using privileged port ({}) without root privileges".format(self.args.lport))
            assoc = ae.associate(self.args.rhost,
                                 self.args.rport,
                                 bind_address=('', self.args.lport),
                                 ae_title=self.args.aetscp)
            TLog.trydo("Server implementation version name ({})".format(assoc.acceptor.implementation_version_name))
            TLog.trydo("Server implementation class UID ({})".format(assoc.acceptor.implementation_class_uid))
            if assoc.is_established:
                responses = assoc.send_c_find(ds, query_model=self.args.model)
                if responses:
                    for (status, identifier) in responses:
                        TLog.success("C-FIND query status: (0x{0:04x})".format(status.Status))
                        # As per pynetdicom if status is either of below, then responses contain valid identifier
                        # datasets, else None. Ref: pynetdicom/pynetdicom/apps/findscu/findscu.py
                        if status.Status in (0xFF00, 0xFF01):
                            TLog.success("C-FIND query Identifier: ({})".format(identifier))
                else:
                    rsn = "Did not receive any response datasets"
                    TLog.fail(rsn)
                    self.result.setstatus(passed=False, reason=rsn)
            else:
                self.result.setstatus(passed=False, reason="Could not establish association with the server")
        except:
            self.result.exception()
        finally:
            if assoc:
                assoc.release()