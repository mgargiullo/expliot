"""Plugin/test details."""
import argparse
from collections import namedtuple
from os import geteuid
import sys

from expliot.core.common.exceptions import sysexcinfo


class TCategory(namedtuple("TCategory", "tech, iface, action")):
    """
    Representation of Test Category.

    The class that defines the category of the test case. It is part of the
    Test class member _category. It can be used to identify the type of test
    or search for a specific category. It is a namedtuple that defines three
    attributes (for categorizing test cases).

    1. tech: What technology does the test use
    2. iface: Interface of the test i.e. whether it is for software or hardware
    3. action: What action does the test perform i.e. is it an exploit or a
               recon test for example.
    """

    # Tech category. The technology used by the test
    # Network Protocols
    COAP = "coap"
    DICOM = "dicom"
    MDNS = "mdns"
    MODBUS = "modbus"
    MQTT = "mqtt"
    UDP = "udp"
    TCP = "tcp"
    HTTP = "http"

# Radio protocols
    BLE = "ble"
    ZIGBEE = "zigbee"
    IEEE802154 = "802154"

    # Hardware protocols
    CAN = "can"
    I2C = "i2c"
    JTAG = "jtag"
    SPI = "spi"
    UART = "uart"

    # Other
    CRYPTO = "crypto"
    # Auditors
    ZB_AUDITOR = "zbauditor"
    BUS_AUDITOR = "busauditor"
    FW_AUDITOR = "fwauditor"

    _tech = [
        BLE,
        BUS_AUDITOR,
        CAN,
        COAP,
        DICOM,
        FW_AUDITOR,
        I2C,
        IEEE802154,
        JTAG,
        MDNS,
        MODBUS,
        MQTT,
        SPI,
        UART,
        UDP,
        TCP,
        HTTP,
        CRYPTO,
        ZB_AUDITOR,
        ZIGBEE,
    ]

# Interface category. Whether the test is for software, hardware or radio
    HW = "hardware"
    RD = "radio"
    SW = "software"

    _interfaces = [SW, HW, RD]

    # Action category. The type of test
    ANALYSIS = "analysis"
    DISCOVERY = "discovery"
    EXPLOIT = "exploit"
    FUZZ = "fuzz"
    RECON = "recon"

    _actions = [RECON, DISCOVERY, ANALYSIS, FUZZ, EXPLOIT]

    def __init__(self, tech, iface, action):
        """Initialize the test category."""
        if tech not in TCategory._tech:
            raise AttributeError("Unknown technology for category - ({})".format(tech))
        if iface not in TCategory._interfaces:
            raise AttributeError("Unknown interface for category - ({})".format(iface))
        if action not in TCategory._actions:
            raise AttributeError("Unknown action for category - ({})".format(action))
        super().__init__()


class TTarget(namedtuple("TTarget", "name, version, vendor")):
    """
    Representation of Test Target class.

    Class that hold details about the target of the test. It is a namedtuple
    and holds the below details:

    1. name - Target/product name
    2. version - Version of the product
    3. vendor - Vendor that owns the product

    Please note, in case it is a generic test case that can be used for
    multiple products use Target.GENERIC for all attributes.
    """

    GENERIC = "generic"

    # Target name
    TP_LINK_IOT = "tpliot"
    AWS = "aws"
    _name = [
        AWS,
    ]

    # Target version

    # Target vendor
    TP_LINK = "tplink"
    AMAZON = "amazon"
    _vendor = [
        AMAZON,
    ]

    def __init__(self, name, version, vendor):
        """Initialize the test target."""
        super().__init__()


class TResult:
    """Representation of a test result."""

    defaultrsn = "No reason specified"

    def __init__(self):
        """Initialize a test result."""
        self.passed = True
        self.reason = None

    def setstatus(self, passed=True, reason=None):
        """Set the Test result status.

        :param passed: True or False
        :param reason: Reason for failure if any
        :return:
        """
        self.passed = passed
        self.reason = reason

    def exception(self):
        """Set passed to False and reason to the exception message.

        :return:
        """
        self.passed = False
        self.reason = "Exception caught: [{}]".format(sysexcinfo())


class TLog:
    """
    Representation of a Test Log.

    Logger class for logging test case output. By default log to sys.stdout
    Must not instantiate. Use class methods. The logger needs to be initialized
    with the output file using init() class method
    """

    _file = sys.stdout
    _success_prefix = "[+]"  # Success prefix
    _fail_prefix = "[-]"  # Fail prefix
    _trydo_prefix = "[?]"  # Try/search prefix
    _generic_prefix = "[*]"  # Generic prefix

    @classmethod
    def init(cls, file=None):
        """
        Initialize the file object. This method should be called in the
        beginning of the application to open the log output file.

        :param file: The file where to log the test output
        :return:
        """
        cls.close()
        if file is None:
            cls._file = sys.stdout
        else:
            cls._file = open(file, mode="w")

    @classmethod
    def close(cls):
        """Close the file object if it is not sys.stdout.

        :return:
        """
        if cls._file != sys.stdout and cls._file is not None:
            cls._file.close()

    @classmethod
    def _print(cls, prefix, message):
        """
        The actual print methods that write the formatted message to the _file
        file.

        :param prefix: the prefix to be used for the message (defined above)
        :param message: The actual message from the Test object
        :return:
        """
        print("{} {}".format(prefix, message), file=cls._file)

    @classmethod
    def success(cls, message):
        """Write a message with success prefix to the file.

        :param message: The message to be written
        :return:
        """
        cls._print(cls._success_prefix, message)

    @classmethod
    def fail(cls, message):
        """Write a message with fail prefix to the file.

        :param message: The message to be written
        :return:
        """
        cls._print(cls._fail_prefix, message)

    @classmethod
    def trydo(cls, message):
        """Write a message with try prefix to the file.

        :param message: The message to be written
        :return: void
        """
        cls._print(cls._trydo_prefix, message)

    @classmethod
    def generic(cls, message):
        """Write a message with success prefix to the file.

        :param message: The message to be written
        :return: void
        """
        cls._print(cls._generic_prefix, message)


class Test:
    """
    Representation of Test.

    The Base class for test cases (plugins). It defines the basic interface
    and basic implementation for the test cases. All test case plugins need
    to inherit from a test class derived from this class or this class itself
    depending on the purpose of the test case.
    """

    def __init__(self, **kwargs):
        """Initialize the test."""
        self.name = kwargs["name"]
        self.summary = kwargs["summary"]
        self.descr = kwargs["descr"]
        self.author = kwargs["author"]
        self.email = kwargs["email"]
        self.ref = kwargs["ref"]
        self.category = kwargs["category"]
        self.target = kwargs["target"]
        self.needroot = kwargs["needroot"] if ("needroot" in kwargs.keys()) else False

        self._setid()
        self.argparser = argparse.ArgumentParser(prog=self.id, description=self.descr)
        self.result = TResult()

        # Namespace returned by self.argparser.parser_args()
        # This gets defined in the run() method and has a getter self.args for inherited class Plugin
        self.args = None

    def pre(self):
        """Action to take before the test."""
        pass
        # TLog.generic("Test base class pre({}) method".format(self.__class__.__name__))

    def post(self):
        """Action to take after the test."""
        pass
        # TLog.generic("Test base class post({}) method".format(self.__class__.__name__))

    def execute(self):
        """Execute the test."""
        print("Test base class execute() method")

    def intro(self):
        """Show the intro for test."""
        TLog.generic("{:<13} {}".format("Test:", self.id))
        TLog.generic("{:<13} {}".format("Author:", self.author))
        TLog.generic("{:<13} {}".format("Author Email:", self.email))
        TLog.generic("{:<13} {}".format("Reference(s):", self.ref))
        TLog.generic(
            "{:<13} Technology={}|Interface={}|Action={}".format(
                "Category:",
                self.category.tech,
                self.category.iface,
                self.category.action,
            )
        )
        TLog.generic(
            "{:<13} Name={}|Version={}|Vendor={}".format(
                "Target:", self.target.name, self.target.version, self.target.vendor
            )
        )
        TLog.generic("")

    def run(self, arglist):
        """
        Run the test.

        Args:
            arglist (list): The argument list of the plugin.

        Returns:
            Nothing.
        """
        try:
            self.args = self.argparser.parse_args(arglist)
        except SystemExit:
            # Nothing to do here. SystemExit occurs in case of wrong arguments or help
            # Cmd2 does not catch SystemExit from v1.0.2 - https://github.com/python-cmd2/cmd2/issues/932
            # returning instead of raising Cmd2ArgparseError so in future any post command hooks implemented can run
            return

        # Log Test Intro messages
        self.intro()

        # Check if the plugin needs root privileges and the program has
        # the required privileges
        self._assertpriv()

        # Test pre() method is used for setup related tasks, if any.
        self.pre()

        # Test execute() method is for the main test case execution.
        self.execute()

        # Test post() method is used for cleanup related tasks, if any.
        self.post()
        # except:
        #    self.result.exception()

        # Log Test status
        self._logstatus()

    def _assertpriv(self):
        """
        Raise an exception if the plugin needs root privileges but program
        is not executing as root.

        Args:
            None

        Returns:
            Nothing
        """
        if self.needroot and geteuid() != 0:
            raise PermissionError(
                "Need root privilege to execute the plugin ({})".format(self.id)
            )

    def _setid(self):
        """
        Set the Unique Test ID. The ID is the plugin class name in lowercase.

        Args:
            None

        Returns:
            Nothing
        """
        # self.id = self.__class__.__name__.lower()
        self.id = "{}.{}.{}".format(
            self.category.tech, self.target.name, self.name
        ).lower()

    def _logstatus(self):
        """
        Handle the log status.

        Args:
            None

        Returns:
            Nothing
        """
        if self.result.passed:
            TLog.success("Test {} passed".format(self.id))
        else:
            TLog.fail("Test {} failed. Reason = {}".format(self.id, self.result.reason))
