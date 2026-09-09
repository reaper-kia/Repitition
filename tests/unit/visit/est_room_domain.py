import pytest
from uuid import uuid4
from datetime import datetime, UTC

# Импорты твоих доменных сущностей и исключений
from src.modules.casino_service.domain.entities import Room, CasinoPlayer
from src.modules.casino_service.domain.enums import RoomStatus, GameType, RoomVisibility
from src.modules.casino_service.domain.exceptions import RoomIsFullError, InvalidRoomStatusTransitionError

class TestRoomDomain:
    
    def test_create_room_success(self):
        """Тест успешного создания комнаты."""
        owner_id = uuid4()
        room = Room.create(
            owner_id=owner_id,
            game_type=GameType.BLACKJACK,
            visibility=RoomVisibility.PUBLIC,
            max_players=4,
        )
        
        assert room.owner_id == owner_id
        assert room.status == RoomStatus.WAITING
        assert room.game_type == GameType.BLACKJACK
        assert len(room.participants) == 0

    def test_add_participant_success(self):
        """Тест успешного добавления участника."""
        room = Room.create(owner_id=uuid4(), game_type=GameType.POKER, visibility=RoomVisibility.PUBLIC, max_players=4)
        player = CasinoPlayer(identity_user_id=uuid4(), balance=1000)
        
        room.add_participant(player)
        
        assert len(room.participants) == 1
        assert room.participants[0].identity_user_id == player.identity_user_id

    def test_add_participant_to_full_room_raises_error(self):
        """Тест: нельзя добавить игрока, если комната заполнена."""
        room = Room.create(owner_id=uuid4(), game_type=GameType.POKER, visibility=RoomVisibility.PUBLIC, max_players=1)
        player1 = CasinoPlayer(identity_user_id=uuid4(), balance=1000)
        player2 = CasinoPlayer(identity_user_id=uuid4(), balance=1000)
        
        room.add_participant(player1)
        
        with pytest.raises(RoomIsFullError):
            room.add_participant(player2)

    def test_close_room_success(self):
        """Тест успешного закрытия комнаты."""
        room = Room.create(owner_id=uuid4(), game_type=GameType.ROULETTE, visibility=RoomVisibility.PRIVATE, max_players=4)
        
        room.close()
        
        assert room.status == RoomStatus.FINISHED

    def test_close_already_finished_room_raises_error(self):
        """Тест: нельзя закрыть уже закрытую комнату."""
        room = Room.create(owner_id=uuid4(), game_type=GameType.ROULETTE, visibility=RoomVisibility.PRIVATE, max_players=4)
        room.close()
        
        with pytest.raises(InvalidRoomStatusTransitionError):
            room.close()