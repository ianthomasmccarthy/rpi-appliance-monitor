import unittest2 as unittest
import mock
from vibration import LaundryMassager


class TestLaundryMassager(unittest.TestCase):

    @mock.patch('vibration.logging')
    def setUp(self, mock_logging):
        # mock_logging.configure_mock()
        self._lm = LaundryMassager()
        self._lm.log = mock.MagicMock()

    def test_simple(self):
        self.assertEquals(1, 1)

    @mock.patch('vibration.time')
    def test_vibrated(self, mock_time):
        mock_time.time.return_value = 1
        self._lm.vibrated(x=0)
        self.assertEquals(self._lm.count, 1)
        self.assertEquals(self._lm.l_vib_time, 1)

#    @unittest.skip("Not the same on Windows")
    def test_convert_timestamp(self):
        td = self._lm.convert_timestamp(0)
        self.assertEquals(td, "Thu Jan  1 00:00:00 1970")
        td = None
        td = self._lm.convert_timestamp(None)
        self.assertEquals(td, "Date Error")

    def test_send_appliance_active(self):
        self._lm.send_alert = mock.MagicMock()
        self._lm.send_appliance_active()
        assert self._lm.send_alert.called

    def test_send_appliance_stopped(self):
        self._lm.send_alert = mock.MagicMock()
        self._lm.send_appliance_stopped(60)
        assert self._lm.send_alert.called

    def test_send_appliance_inactive(self):
        self._lm.send_alert = mock.MagicMock()
        self._lm.send_appliance_inactive()
        assert self._lm.send_alert.called

    @mock.patch('vibration.time')
    def test_start_active(self, mock_time):
        self.assertEquals(self._lm.appliance_active, False)
        mock_time.time.return_value = 1
        self._lm.send_appliance_active = mock.MagicMock()
        self._lm.start_active()
        self.assertTrue(self._lm.appliance_active)
        self.assertEqual(self._lm.s_vib_time, 1)
        assert self._lm.send_appliance_active.called

    @mock.patch('vibration.time')
    def test_should_stop(self, mock_time):
        self._lm.send_appliance_stopped = mock.MagicMock()
        self._lm.appliance_active = True
        mock_time.time.return_value = 10
        self._lm.l_vib_time = 1
        self._lm.stopped_thresh = 1
        self._lm.should_stop()
        self.assertFalse(self._lm.appliance_active)
        assert self._lm.send_appliance_stopped.called

if __name__ == '__main__':
    unittest.main()
